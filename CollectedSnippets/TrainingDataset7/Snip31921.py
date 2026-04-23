async def test_session_load_does_not_create_record_async(self):
        session = self.backend("someunknownkey")
        await session.aload()

        self.assertIsNone(session.session_key)
        self.assertIs(await session.aexists(session.session_key), False)
        # Provided unknown key was cycled, not reused.
        self.assertNotEqual(session.session_key, "someunknownkey")