def b64_encode(s):
    return base64.urlsafe_b64encode(s).strip(b"=")