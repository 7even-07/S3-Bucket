import os
from django.conf import settings

def bucket_path(bucket_name):
    return os.path.join(settings.OBJECT_STORAGE_ROOT, bucket_name)

def object_file_path(bucket_name, key):
    safe_key = os.path.normpath(key).lstrip(os.sep)
    return os.path.join(bucket_path(bucket_name), safe_key)

def save_object_file(bucket_name, key, fileobj):
    path = object_file_path(bucket_name, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # fileobj may be a file-like object
    with open(path, "wb") as f:
        for chunk in iter(lambda: fileobj.read(8192), b""):
            f.write(chunk)
    return path

def delete_object_file(bucket_name, key):
    path = object_file_path(bucket_name, key)
    if os.path.exists(path):
        os.remove(path)
        try:
            parent = os.path.dirname(path)
            while parent != bucket_path(bucket_name) and not os.listdir(parent):
                os.rmdir(parent)
                parent = os.path.dirname(parent)
        except Exception:
            pass
        return True
    return False

def open_object_file(bucket_name, key, mode="rb"):
    return open(object_file_path(bucket_name, key), mode)

def object_exists(bucket_name, key):
    return os.path.exists(object_file_path(bucket_name, key))

def list_objects_under_prefix(bucket_name, prefix=""):
    base = bucket_path(bucket_name)
    results = []
    if os.path.exists(base):
        for root, dirs, files in os.walk(base):
            for fname in files:
                full = os.path.join(root, fname)
                key = os.path.relpath(full, base).replace(os.sep, "/")
                if prefix:
                    if key.startswith(prefix):
                        results.append(key)
                else:
                    results.append(key)
    return results
