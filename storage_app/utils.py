import time
import hmac
import hashlib
from django.conf import settings
from urllib.parse import quote, unquote

def make_presigned_token(bucket, key, expires_in=None):
    expiry = int(time.time()) + (expires_in or settings.PRESIGNED_DEFAULT_EXPIRY_SECONDS)
    payload = f"{bucket}|{key}|{expiry}"
    sig = hmac.new(settings.PRESIGNED_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = f"{payload}|{sig}"
    return quote(token)

def verify_presigned_token(token):
    token = unquote(token)
    try:
        bucket, key, expiry_str, sig = token.split("|")
    except ValueError:
        return False, "invalid"
    expected_payload = f"{bucket}|{key}|{expiry_str}"
    expected_sig = hmac.new(settings.PRESIGNED_KEY.encode(), expected_payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        return False, "bad-signature"
    if int(expiry_str) < int(time.time()):
        return False, "expired"
    return True, {"bucket": bucket, "key": key}
