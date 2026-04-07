def _encode(self, messages, encode_empty=False):
        """
        Return an encoded version of the messages list which can be stored as
        plain text.

        Proxies MessagePartSerializer.dumps and _encoded_parts.
        """
        serialized_messages = MessagePartSerializer().dumps(messages)
        return self._encode_parts(serialized_messages, encode_empty=encode_empty)