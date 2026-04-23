async def aconfigure_user(self, request, user, created=True):
        """See configure_user()"""
        return await sync_to_async(self.configure_user)(request, user, created)