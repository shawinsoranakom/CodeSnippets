def test_context_copyable(self):
        request_context = RequestContext(HttpRequest())
        request_context_copy = copy(request_context)
        self.assertIsInstance(request_context_copy, RequestContext)
        self.assertEqual(request_context_copy.dicts, request_context.dicts)
        self.assertIsNot(request_context_copy.dicts, request_context.dicts)