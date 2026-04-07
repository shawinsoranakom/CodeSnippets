async def aget_expire_at_browser_close(self):
        if (expiry := await self.aget("_session_expiry")) is None:
            return settings.SESSION_EXPIRE_AT_BROWSER_CLOSE
        return expiry == 0