async def test_asend_robust(self):
        class ReceiverException(Exception):
            pass

        receiver_exception = ReceiverException()

        async def failing_async_handler(**kwargs):
            raise receiver_exception

        sync_handler = SyncHandler()
        async_handler = AsyncHandler()
        signal = dispatch.Signal()
        signal.connect(failing_async_handler)
        signal.connect(async_handler)
        signal.connect(sync_handler)
        result = await signal.asend_robust(self.__class__)
        # The ordering here is different than the order that signals were
        # connected in.
        self.assertEqual(
            result,
            [
                (sync_handler, 1),
                (failing_async_handler, receiver_exception),
                (async_handler, 1),
            ],
        )