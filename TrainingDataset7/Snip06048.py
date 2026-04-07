async def aupdate_session_auth_hash(request, user):
    """See update_session_auth_hash()."""
    await request.session.acycle_key()
    if hasattr(user, "get_session_auth_hash") and await request.auser() == user:
        await request.session.aset(HASH_SESSION_KEY, user.get_session_auth_hash())