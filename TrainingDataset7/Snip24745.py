async def test_unawaited_response(self):
        msg = (
            "The view handlers.views.CoroutineClearingView.__call__ didn't"
            " return an HttpResponse object. It returned an unawaited"
            " coroutine instead. You may need to add an 'await'"
            " into your view."
        )
        with self.assertRaisesMessage(ValueError, msg):
            await self.async_client.get("/unawaited/")