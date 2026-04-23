def test_request_after_client(self):
        # apart from the next line the three tests are identical
        self.client.get("/")
        self.common_test_that_should_always_pass()