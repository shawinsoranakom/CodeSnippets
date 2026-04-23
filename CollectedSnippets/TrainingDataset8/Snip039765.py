async def test_handle_backmsg(self):
        """BackMsgs should be delivered to the appropriate AppSession."""
        with self.patch_app_session():
            await self.runtime.start()
            session_id = self.runtime.create_session(
                client=MockSessionClient(), user_info=MagicMock()
            )

            back_msg = MagicMock()
            self.runtime.handle_backmsg(session_id, back_msg)

            app_session = self.runtime._get_session_info(session_id).session
            app_session.handle_backmsg.assert_called_once_with(back_msg)