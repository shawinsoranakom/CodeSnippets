def write_forward_msg(self, msg: ForwardMsg) -> None:
        """Send a ForwardMsg to the browser."""
        try:
            self.write_message(serialize_forward_msg(msg), binary=True)
        except tornado.websocket.WebSocketClosedError as e:
            raise SessionClientDisconnectedError from e