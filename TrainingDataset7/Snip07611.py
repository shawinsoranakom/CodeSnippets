def loads(self, data):
        return json.loads(data.decode("latin-1"), cls=MessageDecoder)