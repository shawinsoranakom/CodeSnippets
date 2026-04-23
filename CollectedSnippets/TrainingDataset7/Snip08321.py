def delete(self, key):
        client = self.get_client(key, write=True)
        return bool(client.delete(key))