def loads(
    s,
    key=None,
    salt="django.core.signing",
    serializer=JSONSerializer,
    max_age=None,
    fallback_keys=None,
):
    """
    Reverse of dumps(), raise BadSignature if signature fails.

    The serializer is expected to accept a bytestring.
    """
    return TimestampSigner(
        key=key, salt=salt, fallback_keys=fallback_keys
    ).unsign_object(
        s,
        serializer=serializer,
        max_age=max_age,
    )