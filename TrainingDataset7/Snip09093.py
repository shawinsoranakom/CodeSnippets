def _cookie_signer_key(key):
    # SECRET_KEYS items may be str or bytes.
    return b"django.http.cookies" + force_bytes(key)