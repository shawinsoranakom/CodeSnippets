async def ws_connect(self) -> WebSocketClientConnection:
        """Open a websocket connection to the server.

        Returns
        -------
        WebSocketClientConnection
            The connected websocket client.

        """
        return await tornado.websocket.websocket_connect(self.get_ws_url("/stream"))