async def alogout(request):
    """See logout()."""
    # Dispatch the signal before the user is logged out so the receivers have a
    # chance to find out *who* logged out.
    user = getattr(request, "auser", None)
    if user is not None:
        user = await user()
        if not getattr(user, "is_authenticated", True):
            user = None
    await user_logged_out.asend(sender=user.__class__, request=request, user=user)
    await request.session.aflush()

    has_user = hasattr(request, "user")
    has_auser = hasattr(request, "auser")
    if has_user or has_auser:
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        if has_user:
            request.user = anon
        if has_auser:

            async def auser():
                return anon

            request.auser = auser