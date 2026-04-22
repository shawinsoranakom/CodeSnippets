def get(self):
        msg_hash = self.get_argument("hash", None)
        if msg_hash is None:
            # Hash is missing! This is a malformed request.
            _LOGGER.error(
                "HTTP request for cached message is missing the hash attribute."
            )
            self.set_status(404)
            raise tornado.web.Finish()

        message = self._cache.get_message(msg_hash)
        if message is None:
            # Message not in our cache.
            _LOGGER.error(
                "HTTP request for cached message could not be fulfilled. "
                "No such message"
            )
            self.set_status(404)
            raise tornado.web.Finish()

        _LOGGER.debug("MessageCache HIT")
        msg_str = serialize_forward_msg(message)
        self.set_header("Content-Type", "application/octet-stream")
        self.write(msg_str)
        self.set_status(200)