def deserialize_messages(self, data):
        if data and isinstance(data, str):
            return json.loads(data, cls=MessageDecoder)
        return data