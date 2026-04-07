async def alogin(request, user, backend=None):
    """See login()."""
    session_auth_hash = user.get_session_auth_hash()

    if await request.session.ahas_key(SESSION_KEY):
        if await _aget_user_session_key(request) != user.pk or (
            session_auth_hash
            and not constant_time_compare(
                await request.session.aget(HASH_SESSION_KEY, ""),
                session_auth_hash,
            )
        ):
            # To avoid reusing another user's session, create a new, empty
            # session if the existing session corresponds to a different
            # authenticated user.
            await request.session.aflush()
    else:
        await request.session.acycle_key()

    backend = _get_backend_from_user(user=user, backend=backend)

    await request.session.aset(SESSION_KEY, user._meta.pk.value_to_string(user))
    await request.session.aset(BACKEND_SESSION_KEY, backend)
    await request.session.aset(HASH_SESSION_KEY, session_auth_hash)
    if hasattr(request, "user"):
        request.user = user
    if hasattr(request, "auser"):

        async def auser():
            return user

        request.auser = auser
    rotate_token(request)
    await user_logged_in.asend(sender=user.__class__, request=request, user=user)