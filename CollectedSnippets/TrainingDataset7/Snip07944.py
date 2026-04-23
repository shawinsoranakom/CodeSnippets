async def aget_expiry_age(self, **kwargs):
        try:
            modification = kwargs["modification"]
        except KeyError:
            modification = timezone.now()
        try:
            expiry = kwargs["expiry"]
        except KeyError:
            expiry = await self.aget("_session_expiry")

        if not expiry:  # Checks both None and 0 cases
            return self.get_session_cookie_age()
        if not isinstance(expiry, (datetime, str)):
            return expiry
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry)
        delta = expiry - modification
        return delta.days * 86400 + delta.seconds