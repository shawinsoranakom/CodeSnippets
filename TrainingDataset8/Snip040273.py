async def test_backmsg_deserialization_exception(self):
        """If BackMsg deserialization raises an Exception, we should call the Runtime's
        handler.
        """
        with self._patch_app_session():
            await self.server.start()
            await self.ws_connect()

            # Get our BrowserWebSocketHandler
            session_info = list(self.server._runtime._session_info_by_id.values())[0]
            websocket_handler: BrowserWebSocketHandler = session_info.client

            mock_runtime = MagicMock(spec=Runtime)
            websocket_handler._runtime = mock_runtime

            # Send a malformed BackMsg
            websocket_handler.on_message(b"NotABackMsg")

            mock_runtime.handle_backmsg_deserialization_exception.assert_called_once()
            mock_runtime.handle_backmsg.assert_not_called()