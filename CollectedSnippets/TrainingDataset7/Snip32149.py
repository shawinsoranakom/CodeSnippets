async def test_asend_robust_only_async_receivers(self):
        async_handler = AsyncHandler()
        signal = dispatch.Signal()
        signal.connect(async_handler)

        result = await signal.asend_robust(self.__class__)
        self.assertEqual(result, [(async_handler, 1)])