def base64_hmac(salt, value, key, algorithm="sha1"):
    return b64_encode(
        salted_hmac(salt, value, key, algorithm=algorithm).digest()
    ).decode()