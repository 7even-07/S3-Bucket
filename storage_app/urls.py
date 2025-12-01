from django.urls import path
from . import views

urlpatterns = [
    path("buckets/", views.BucketListCreateView.as_view(), name="buckets-list-create"),
    path("buckets/<str:name>/", views.BucketDeleteView.as_view(), name="bucket-delete"),
    path("buckets/<str:bucket_name>/files/", views.ObjectListView.as_view(), name="file-list"),
    path("buckets/<str:bucket_name>/files/upload/", views.ObjectUploadView.as_view(), name="file-upload-post"),
    path("buckets/<str:bucket_name>/files/<path:key>/download/", views.ObjectDownloadView.as_view(), name="file-download"),
    path("buckets/<str:bucket_name>/files/<path:key>/delete/", views.ObjectDeleteView.as_view(), name="file-delete"),
    path("buckets/<str:bucket_name>/files/<path:key>/presign/", views.PresignView.as_view(), name="presign"),
    path("buckets/<str:bucket_name>/files/<path:key>/", views.ObjectUploadView.as_view(), name="file-upload-put"),
    path("presigned/<path:token>/", views.PresignedDownloadView.as_view(), name="presigned-download"),
]
