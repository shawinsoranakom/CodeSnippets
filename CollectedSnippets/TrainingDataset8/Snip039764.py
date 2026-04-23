async def test_shutdown_appsessions_on_stop(self):
        """When the Runtime stops, it should shut down open AppSessions."""
        with self.patch_app_session():
            await self.runtime.start()

            # Create a few sessions
            app_sessions = []
            for _ in range(3):
                session_id = self.runtime.create_session(
                    MockSessionClient(), MagicMock()
                )
                app_session = self.runtime._get_session_info(session_id).session
                app_sessions.append(app_session)

            # Sanity check
            for app_session in app_sessions:
                app_session.shutdown.assert_not_called()

            # Stop the Runtime
            self.runtime.stop()
            await self.runtime.stopped

            # All sessions should be shut down
            self.assertEqual(RuntimeState.STOPPED, self.runtime.state)
            for app_session in app_sessions:
                app_session.shutdown.assert_called_once()