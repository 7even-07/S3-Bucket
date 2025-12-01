from rest_framework import serializers
from .models import Bucket, ObjectMetadata

class BucketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bucket
        fields = ("id", "name", "created_at")

class ObjectMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectMetadata
        fields = ("id", "bucket", "key", "content_type", "size", "created_at", "updated_at")
        read_only_fields = ("size", "created_at", "updated_at")
