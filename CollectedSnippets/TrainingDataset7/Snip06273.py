async def _aremove_invalid_user(self, request):
        """
        Remove the current authenticated user in the request which is invalid
        but only if the user is authenticated via the RemoteUserBackend.
        """
        try:
            stored_backend = load_backend(
                await request.session.aget(auth.BACKEND_SESSION_KEY, "")
            )
        except ImportError:
            # Backend failed to load.
            await auth.alogout(request)
        else:
            if isinstance(stored_backend, RemoteUserBackend):
                await auth.alogout(request)