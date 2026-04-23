async def aget_user(request):
    """See get_user()."""
    from .models import AnonymousUser

    user = None
    try:
        user_id = await _aget_user_session_key(request)
        backend_path = await request.session.aget(BACKEND_SESSION_KEY)
    except KeyError:
        pass
    else:
        if backend_path in settings.AUTHENTICATION_BACKENDS:
            backend = load_backend(backend_path)
            user = await backend.aget_user(user_id)
            # Verify the session
            if hasattr(user, "get_session_auth_hash"):
                session_hash = await request.session.aget(HASH_SESSION_KEY)
                if not session_hash:
                    session_hash_verified = False
                else:
                    session_auth_hash = user.get_session_auth_hash()
                    session_hash_verified = constant_time_compare(
                        session_hash, session_auth_hash
                    )
                if not session_hash_verified:
                    # If the current secret does not verify the session, try
                    # with the fallback secrets and stop when a matching one is
                    # found.
                    if session_hash and any(
                        constant_time_compare(session_hash, fallback_auth_hash)
                        for fallback_auth_hash in user.get_session_auth_fallback_hash()
                    ):
                        await request.session.acycle_key()
                        await request.session.aset(HASH_SESSION_KEY, session_auth_hash)
                    else:
                        await request.session.aflush()
                        user = None

    return user or AnonymousUser()