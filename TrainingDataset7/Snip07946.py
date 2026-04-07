async def aget_expiry_date(self, **kwargs):
        try:
            modification = kwargs["modification"]
        except KeyError:
            modification = timezone.now()
        try:
            expiry = kwargs["expiry"]
        except KeyError:
            expiry = await self.aget("_session_expiry")

        if isinstance(expiry, datetime):
            return expiry
        elif isinstance(expiry, str):
            return datetime.fromisoformat(expiry)
        expiry = expiry or self.get_session_cookie_age()
        return modification + timedelta(seconds=expiry)