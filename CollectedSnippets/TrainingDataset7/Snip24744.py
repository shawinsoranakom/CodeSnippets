async def test_no_response(self):
        msg = (
            "The view handlers.views.no_response didn't return an "
            "HttpResponse object. It returned None instead."
        )
        with self.assertRaisesMessage(ValueError, msg):
            await self.async_client.get("/no_response_fbv/")