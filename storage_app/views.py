import os
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from .models import Bucket, ObjectMetadata
from .serializers import BucketSerializer
from . import storage_backend
from .utils import make_presigned_token, verify_presigned_token

class BucketListCreateView(generics.ListCreateAPIView):
    queryset = Bucket.objects.all()
    serializer_class = BucketSerializer

    def perform_create(self, serializer):
        bucket = serializer.save()
        os.makedirs(storage_backend.bucket_path(bucket.name), exist_ok=True)

class BucketDeleteView(APIView):
    def delete(self, request, name):
        bucket = get_object_or_404(Bucket, name=name)
        base = storage_backend.bucket_path(bucket.name)
        if os.path.exists(base):
            import shutil
            shutil.rmtree(base)
        bucket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ObjectListView(APIView):
    def get(self, request, bucket_name):
        bucket = get_object_or_404(Bucket, name=bucket_name)
        prefix = request.query_params.get("prefix", "")
        keys = storage_backend.list_objects_under_prefix(bucket.name, prefix)
        metas = []
        for key in keys:
            try:
                meta = ObjectMetadata.objects.get(bucket=bucket, key=key)
                metas.append({
                    "key": key,
                    "size": meta.size,
                    "content_type": meta.content_type,
                    "updated_at": meta.updated_at,
                })
            except ObjectMetadata.DoesNotExist:
                metas.append({"key": key})
        return Response(metas)

from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import io

class ObjectUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, bucket_name):
        bucket = get_object_or_404(Bucket, name=bucket_name)
        f = request.FILES.get("file")
        if not f:
            return Response({"detail":"No file part 'file' uploaded."}, status=400)
        key = request.data.get("key") or f.name
        storage_backend.save_object_file(bucket.name, key, f)
        ObjectMetadata.objects.update_or_create(
            bucket=bucket, key=key,
            defaults={"content_type": f.content_type or "", "size": f.size}
        )
        return Response({"key": key, "size": f.size}, status=201)

    def put(self, request, bucket_name, key):
        bucket = get_object_or_404(Bucket, name=bucket_name)
        body = request.body
        import io
        body_stream = io.BytesIO(body)
        storage_backend.save_object_file(bucket.name, key, body_stream)
        size = os.path.getsize(storage_backend.object_file_path(bucket.name, key))
        ObjectMetadata.objects.update_or_create(
            bucket=bucket, key=key,
            defaults={"content_type": request.content_type or "", "size": size}
        )
        return Response({"key": key, "size": size}, status=201)

class ObjectDownloadView(APIView):
    """Handles file download from a given bucket."""

    def get(self, request, bucket_name, key):
        # 1️⃣ Find the bucket
        bucket = get_object_or_404(Bucket, name=bucket_name)

        # 2️⃣ Find the metadata for this key
        try:
            obj = ObjectMetadata.objects.get(bucket=bucket, key=key)
        except ObjectMetadata.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        # 3️⃣ Get the file path using our storage backend
        file_path = storage_backend.object_file_path(bucket.name, key)

        # 4️⃣ Ensure the file actually exists
        if not os.path.exists(file_path):
            return Response({"error": "File not found on disk"}, status=status.HTTP_404_NOT_FOUND)

        # 5️⃣ Return the file as a downloadable response
        response = FileResponse(open(file_path, "rb"), content_type=obj.content_type or "application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{os.path.basename(key)}"'
        return response

class ObjectDeleteView(APIView):
    def delete(self, request, bucket_name, key):
        bucket = get_object_or_404(Bucket, name=bucket_name)
        deleted = storage_backend.delete_object_file(bucket.name, key)
        ObjectMetadata.objects.filter(bucket=bucket, key=key).delete()
        if deleted:
            return Response(status=204)
        return Response({"detail":"Not found"}, status=404)

class PresignView(APIView):
    def post(self, request, bucket_name, key):
        expires = int(request.data.get("expires", settings.PRESIGNED_DEFAULT_EXPIRY_SECONDS))
        token = make_presigned_token(bucket_name, key, expires)
        host = request.build_absolute_uri("/")[:-1].rstrip("/")
        url = f"{host}/presigned/{token}"
        return Response({"url": url, "expires_in": expires})

from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

class PresignedDownloadView(APIView):
    def get(self, request, token):
        token = unquote(token)
        logger.warning(f"Presigned token received: {token}")

        ok, payload = verify_presigned_token(token)
        logger.warning(f"Verify result: ok={ok}, payload={payload}")

        if not ok:
            return Response({"detail": "invalid or expired token", "reason": payload}, status=403)

        bucket = payload["bucket"]
        key = payload["key"]

        if not storage_backend.object_exists(bucket, key):
            logger.warning(f"File not found: {bucket}/{key}")
            raise Http404("File not found")

        path = storage_backend.object_file_path(bucket, key)
        logger.warning(f"Serving file from: {path}")

        return FileResponse(open(path, "rb"), as_attachment=True, filename=os.path.basename(path))
    def get(self, request, token):
        # Decode token from URL encoding
        token = unquote(token)

        ok, payload = verify_presigned_token(token)
        if not ok:
            return Response({"detail": "invalid or expired token", "reason": payload}, status=403)

        bucket = payload["bucket"]
        key = payload["key"]

        if not storage_backend.object_exists(bucket, key):
            return Response({"detail": "Not found"}, status=404)

        path = storage_backend.object_file_path(bucket, key)

        # Return file in binary-safe mode
        file = open(path, "rb")
        response = FileResponse(file, as_attachment=True, filename=os.path.basename(path))
        return response