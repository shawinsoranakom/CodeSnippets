def set_many(self, data, timeout):
        client = self.get_client(None, write=True)
        pipeline = client.pipeline()
        pipeline.mset({k: self._serializer.dumps(v) for k, v in data.items()})

        if timeout is not None:
            # Setting timeout for each key as redis does not support timeout
            # with mset().
            for key in data:
                pipeline.expire(key, timeout)
        pipeline.execute()