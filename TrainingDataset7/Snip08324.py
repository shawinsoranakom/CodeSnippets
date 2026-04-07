def incr(self, key, delta):
        client = self.get_client(key, write=True)
        if not client.exists(key):
            raise ValueError("Key '%s' not found." % key)
        return client.incr(key, delta)