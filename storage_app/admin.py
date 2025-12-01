from django.contrib import admin
from .models import Bucket, ObjectMetadata

admin.site.register(Bucket)
admin.site.register(ObjectMetadata)
