async def _aget_user_session_key(request):
    # This value in the session is always serialized to a string, so we need
    # to convert it back to Python whenever we access it.
    session_key = await request.session.aget(SESSION_KEY)
    if session_key is None:
        raise KeyError()
    return get_user_model()._meta.pk.to_python(session_key)