def test_auto_transaction(self):
        old_atomic_requests = connection.settings_dict["ATOMIC_REQUESTS"]
        try:
            connection.settings_dict["ATOMIC_REQUESTS"] = True
            response = self.client.get("/in_transaction/")
        finally:
            connection.settings_dict["ATOMIC_REQUESTS"] = old_atomic_requests
        self.assertContains(response, "True")