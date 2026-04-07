async def alogin(self, **credentials):
        """See login()."""
        from django.contrib.auth import aauthenticate

        user = await aauthenticate(**credentials)
        if user:
            await self._alogin(user)
            return True
        return False