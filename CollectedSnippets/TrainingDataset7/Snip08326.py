def delete_many(self, keys):
        client = self.get_client(None, write=True)
        client.delete(*keys)