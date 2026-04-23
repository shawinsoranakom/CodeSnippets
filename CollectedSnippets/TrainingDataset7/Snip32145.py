def test_send(self):
        sync_handler = SyncHandler()
        async_handler = AsyncHandler()
        signal = dispatch.Signal()
        signal.connect(sync_handler)
        signal.connect(async_handler)
        result = signal.send(self.__class__)
        self.assertEqual(result, [(sync_handler, 1), (async_handler, 1)])