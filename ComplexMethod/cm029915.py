def digest(key, msg, digest):
    """Fast inline implementation of HMAC.

    key: bytes or buffer, The key for the keyed hash object.
    msg: bytes or buffer, Input message.
    digest: A hash name suitable for hashlib.new() for best performance. *OR*
            A hashlib constructor returning a new hash object. *OR*
            A module supporting PEP 247.
    """
    if _hashopenssl and isinstance(digest, (str, _functype)):
        try:
            return _hashopenssl.hmac_digest(key, msg, digest)
        except OverflowError:
            # OpenSSL's HMAC limits the size of the key to INT_MAX.
            # Instead of falling back to HACL* implementation which
            # may still not be supported due to a too large key, we
            # directly switch to the pure Python fallback instead
            # even if we could have used streaming HMAC for small keys
            # but large messages.
            return _compute_digest_fallback(key, msg, digest)
        except _hashopenssl.UnsupportedDigestmodError:
            pass

    if _hmac and isinstance(digest, str):
        try:
            return _hmac.compute_digest(key, msg, digest)
        except (OverflowError, _hmac.UnknownHashError):
            # HACL* HMAC limits the size of the key to UINT32_MAX
            # so we fallback to the pure Python implementation even
            # if streaming HMAC may have been used for small keys
            # and large messages.
            pass

    return _compute_digest_fallback(key, msg, digest)