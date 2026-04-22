async def read_forward_msg(
        self, ws_client: WebSocketClientConnection
    ) -> ForwardMsg:
        """Parse the next message from a Websocket client into a ForwardMsg."""
        data = await ws_client.read_message()
        message = ForwardMsg()
        message.ParseFromString(data)
        return message