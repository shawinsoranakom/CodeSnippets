async def aset_expiry(self, value):
        if value is None:
            # Remove any custom expiration for this session.
            try:
                await self.apop("_session_expiry")
            except KeyError:
                pass
            return
        if isinstance(value, timedelta):
            value = timezone.now() + value
        if isinstance(value, datetime):
            value = value.isoformat()
        await self.aset("_session_expiry", value)