async def test_write_forward_msg_reraises_websocket_closed_error(self):
        """`write_forward_msg` should re-raise WebSocketClosedError as
        as SessionClientDisconnectedError.
        """

        with self._patch_app_session():
            await self.server.start()
            await self.ws_connect()

            # Get our connected BrowserWebSocketHandler
            session_info = list(self.server._runtime._session_info_by_id.values())[0]
            websocket_handler = session_info.client
            self.assertIsInstance(websocket_handler, BrowserWebSocketHandler)

            # Patch _BrowserWebSocketHandler.write_message to raise an error
            with mock.patch.object(
                websocket_handler, "write_message"
            ) as write_message_mock:
                write_message_mock.side_effect = tornado.websocket.WebSocketClosedError

                msg = ForwardMsg()
                msg.script_finished = (
                    ForwardMsg.ScriptFinishedStatus.FINISHED_SUCCESSFULLY
                )

                # Send a ForwardMsg. write_message will raise a
                # WebSocketClosedError, and write_forward_msg should re-raise
                # it as a SessionClientDisconnectedError.
                with self.assertRaises(SessionClientDisconnectedError):
                    websocket_handler.write_forward_msg(msg)

                write_message_mock.assert_called_once()