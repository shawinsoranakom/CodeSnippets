async def listen_for_disconnect(self, receive):
        """Listen for disconnect from the client."""
        message = await receive()
        if message["type"] == "http.disconnect":
            raise RequestAborted()
        # This should never happen.
        assert False, "Invalid ASGI message after request body: %s" % message["type"]