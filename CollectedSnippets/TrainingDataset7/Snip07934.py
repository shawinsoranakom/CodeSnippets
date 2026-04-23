async def _aget_new_session_key(self):
        while True:
            session_key = get_random_string(32, VALID_KEY_CHARS)
            if not await self.aexists(session_key):
                return session_key