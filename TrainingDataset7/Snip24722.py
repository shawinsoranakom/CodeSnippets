def test_no_auto_transaction(self):
        old_atomic_requests = connection.settings_dict["ATOMIC_REQUESTS"]
        try:
            connection.settings_dict["ATOMIC_REQUESTS"] = True
            response = self.client.get("/not_in_transaction/")
        finally:
            connection.settings_dict["ATOMIC_REQUESTS"] = old_atomic_requests
        self.assertContains(response, "False")
        try:
            connection.settings_dict["ATOMIC_REQUESTS"] = True
            response = self.client.get("/not_in_transaction_using_none/")
        finally:
            connection.settings_dict["ATOMIC_REQUESTS"] = old_atomic_requests
        self.assertContains(response, "False")
        try:
            connection.settings_dict["ATOMIC_REQUESTS"] = True
            response = self.client.get("/not_in_transaction_using_text/")
        finally:
            connection.settings_dict["ATOMIC_REQUESTS"] = old_atomic_requests
        # The non_atomic_requests decorator is used for an incorrect table.
        self.assertContains(response, "True")