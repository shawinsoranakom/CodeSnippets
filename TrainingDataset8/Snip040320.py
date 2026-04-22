async def test_send_message_to_disconnected_websocket(self):
        """Sending a message to a disconnected SessionClient raises an error.
        We should gracefully handle the error by cleaning up the session.
        """
        with _patch_local_sources_watcher(), self._patch_app_session():
            await self.server.start()
            await self.ws_connect()

            # Get the server's socket and session for this client
            session_info = list(self.server._runtime._session_info_by_id.values())[0]

            with patch.object(
                session_info.session, "flush_browser_queue"
            ) as flush_browser_queue, patch.object(
                session_info.client, "write_message"
            ) as ws_write_message:
                # Patch flush_browser_queue to simulate a pending message.
                flush_browser_queue.return_value = [create_dataframe_msg([1, 2, 3])]

                # Patch the session's WebsocketHandler to raise a
                # WebSocketClosedError when we write to it.
                ws_write_message.side_effect = tornado.websocket.WebSocketClosedError()

                # Tick the server. Our session's browser_queue will be flushed,
                # and the Websocket client's write_message will be called,
                # raising our WebSocketClosedError.
                while not flush_browser_queue.called:
                    self.server._runtime._get_async_objs().need_send_data.set()
                    await asyncio.sleep(0)

                flush_browser_queue.assert_called_once()
                ws_write_message.assert_called_once()

                # Our session should have been removed from the server as
                # a result of the WebSocketClosedError.
                self.assertIsNone(
                    self.server._runtime._get_session_info(session_info.session.id)
                )