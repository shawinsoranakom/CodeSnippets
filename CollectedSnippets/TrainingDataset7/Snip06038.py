async def aauthenticate(request=None, **credentials):
    """See authenticate()."""
    for backend, backend_path in _get_compatible_backends(request, **credentials):
        try:
            user = await backend.aauthenticate(request, **credentials)
        except PermissionDenied:
            # This backend says to stop in our tracks - this user should not be
            # allowed in at all.
            break
        if user is None:
            continue
        # Annotate the user object with the path of the backend.
        user.backend = backend_path
        return user

    # The credentials supplied are invalid to all backends, fire signal.
    await user_login_failed.asend(
        sender=__name__, credentials=_clean_credentials(credentials), request=request
    )