def test_copy_request_context_twice(self):
        """
        #24273 -- Copy twice shouldn't raise an exception
        """
        RequestContext(HttpRequest()).new().new()