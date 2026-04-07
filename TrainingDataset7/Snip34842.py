def common_test_that_should_always_pass(self):
        request = RequestFactory().get("/")
        request.session = {}
        self.assertFalse(hasattr(request, "user"))