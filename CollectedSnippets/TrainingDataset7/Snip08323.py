def has_key(self, key):
        client = self.get_client(key)
        return bool(client.exists(key))