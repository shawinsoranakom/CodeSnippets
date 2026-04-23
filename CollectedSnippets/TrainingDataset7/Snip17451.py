def test_options_handler_responds_correctly(self):
        tests = [
            (SyncView, False),
            (AsyncView, True),
        ]
        for view_cls, is_coroutine in tests:
            with self.subTest(view_cls=view_cls, is_coroutine=is_coroutine):
                instance = view_cls()
                response = instance.options(None)
                self.assertIs(
                    asyncio.iscoroutine(response),
                    is_coroutine,
                )
                if is_coroutine:
                    response = asyncio.run(response)

                self.assertIsInstance(response, HttpResponse)