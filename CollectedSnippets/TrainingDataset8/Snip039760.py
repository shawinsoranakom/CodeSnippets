async def test_close_session_shuts_down_appsession(self):
        """Closing a session should shutdown its associated AppSession."""
        with self.patch_app_session():
            await self.runtime.start()

            # Create a session and get its associated AppSession object.
            session_id = self.runtime.create_session(
                client=MockSessionClient(), user_info=MagicMock()
            )
            app_session = self.runtime._get_session_info(session_id).session

            # Close the session. AppSession.shutdown should be called.
            self.runtime.close_session(session_id)
            app_session.shutdown.assert_called_once()