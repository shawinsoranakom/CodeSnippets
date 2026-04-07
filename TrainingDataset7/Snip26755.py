def test_not_sync_or_async_middleware(self):
        msg = (
            "Middleware "
            "middleware_exceptions.middleware.NotSyncOrAsyncMiddleware must "
            "have at least one of sync_capable/async_capable set to True."
        )
        with self.assertRaisesMessage(RuntimeError, msg):
            self.client.get("/middleware_exceptions/view/")