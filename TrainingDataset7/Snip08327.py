def clear(self):
        client = self.get_client(None, write=True)
        return bool(client.flushdb())