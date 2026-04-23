def encode_decode(self, *args, **kwargs):
        storage = self.get_storage()
        message = [Message(constants.DEBUG, *args, **kwargs)]
        encoded = storage._encode(message)
        return storage._decode(encoded)[0]