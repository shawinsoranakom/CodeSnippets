def serialize_messages(self, messages):
        encoder = MessageEncoder()
        return encoder.encode(messages)