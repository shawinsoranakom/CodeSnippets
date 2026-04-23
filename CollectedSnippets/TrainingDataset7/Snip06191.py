async def acheck_password(password, encoded, setter=None, preferred="default"):
    """See check_password()."""
    is_correct, must_update = await sync_to_async(
        verify_password,
        thread_sensitive=False,
    )(password, encoded, preferred=preferred)
    if setter and is_correct and must_update:
        await setter(password)
    return is_correct