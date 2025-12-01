from django.db import models

class Bucket(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ObjectMetadata(models.Model):
    bucket = models.ForeignKey(Bucket, on_delete=models.CASCADE, related_name="files")
    key = models.TextField()
    content_type = models.CharField(max_length=255, blank=True, default="")
    size = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("bucket", "key")

    def __str__(self):
        return f"{self.bucket.name}/{self.key}"
