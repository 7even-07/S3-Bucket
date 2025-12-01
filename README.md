# s3clone - Minimal S3-like object store (Django)

## Quick start (local)

1. Extract the zip and enter the folder:
   ```
   unzip s3clone.zip
   cd s3clone
   ```

2. Create virtualenv and install requirements
   ```
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Make sure `object_storage` directory exists (it will be auto-created during bucket creation, but you can create now):
   ```
   mkdir -p object_storage
   ```

4. Run migrations and start server:
   ```
   python manage.py migrate
   python manage.py runserver
   ```

5. API base: http://127.0.0.1:8000/api/

See the original chat for detailed endpoint examples (create bucket, upload file, download, presign, etc.)
