def test_middleware_initialized(self):
        handler = WSGIHandler()
        self.assertIsNotNone(handler._middleware_chain)