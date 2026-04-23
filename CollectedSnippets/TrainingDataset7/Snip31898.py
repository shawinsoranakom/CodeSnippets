async def test_invalid_key_async(self):
        # Submitting an invalid session key (either by guessing, or if the db
        # has removed the key) results in a new key being generated.
        try:
            session = self.backend("1")
            await session.asave()
            self.assertNotEqual(session.session_key, "1")
            self.assertIsNone(await session.aget("cat"))
            await session.adelete()
        finally:
            # Some backends leave a stale cache entry for the invalid
            # session key; make sure that entry is manually deleted
            await session.adelete("1")