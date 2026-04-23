def get_many(self, keys):
        client = self.get_client(None)
        ret = client.mget(keys)
        return {
            k: self._serializer.loads(v) for k, v in zip(keys, ret) if v is not None
        }