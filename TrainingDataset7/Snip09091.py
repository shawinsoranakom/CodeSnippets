def b64_decode(s):
    pad = b"=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)