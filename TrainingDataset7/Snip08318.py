def get(self, key, default):
        client = self.get_client(key)
        value = client.get(key)
        return default if value is None else self._serializer.loads(value)