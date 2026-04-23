async def test_auto_transaction_async_view(self):
        old_atomic_requests = connection.settings_dict["ATOMIC_REQUESTS"]
        try:
            connection.settings_dict["ATOMIC_REQUESTS"] = True
            msg = "You cannot use ATOMIC_REQUESTS with async views."
            with self.assertRaisesMessage(RuntimeError, msg):
                await self.async_client.get("/async_regular/")
        finally:
            connection.settings_dict["ATOMIC_REQUESTS"] = old_atomic_requests