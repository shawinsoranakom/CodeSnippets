def __init__(self, message=None):
        """Initialize a Message instance."""
        if isinstance(message, email.message.Message):
            self._become_message(copy.deepcopy(message))
            if isinstance(message, Message):
                message._explain_to(self)
        elif isinstance(message, bytes):
            self._become_message(email.message_from_bytes(message))
        elif isinstance(message, str):
            self._become_message(email.message_from_string(message))
        elif isinstance(message, io.TextIOWrapper):
            self._become_message(email.message_from_file(message))
        elif hasattr(message, "read"):
            self._become_message(email.message_from_binary_file(message))
        elif message is None:
            email.message.Message.__init__(self)
        else:
            raise TypeError('Invalid message type: %s' % type(message))