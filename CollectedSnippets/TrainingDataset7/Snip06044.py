def get_user(request):
    """
    Return the user model instance associated with the given request session.
    If no user is retrieved, return an instance of `AnonymousUser`.
    """
    from .models import AnonymousUser

    user = None
    try:
        user_id = _get_user_session_key(request)
        backend_path = request.session[BACKEND_SESSION_KEY]
    except KeyError:
        pass
    else:
        if backend_path in settings.AUTHENTICATION_BACKENDS:
            backend = load_backend(backend_path)
            user = backend.get_user(user_id)
            # Verify the session
            if hasattr(user, "get_session_auth_hash"):
                session_hash = request.session.get(HASH_SESSION_KEY)
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
                        request.session.cycle_key()
                        request.session[HASH_SESSION_KEY] = session_auth_hash
                    else:
                        request.session.flush()
                        user = None

    return user or AnonymousUser()