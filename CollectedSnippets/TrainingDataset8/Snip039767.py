async def test_handle_backmsg_deserialization_exception(self):
        """BackMsg deserialization Exceptions should be delivered to the
        appropriate AppSession.
        """
        with self.patch_app_session():
            await self.runtime.start()
            session_id = self.runtime.create_session(
                client=MockSessionClient(), user_info=MagicMock()
            )

            exception = MagicMock()
            self.runtime.handle_backmsg_deserialization_exception(session_id, exception)

            app_session = self.runtime._get_session_info(session_id).session
            app_session.handle_backmsg_exception.assert_called_once_with(exception)