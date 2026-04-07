def test_stack_size(self):
        """Optimized RequestContext construction (#7116)."""
        request = self.request_factory.get("/")
        ctx = RequestContext(request, {})
        # The stack contains 4 items:
        # [builtins, supplied context, context processor, empty dict]
        self.assertEqual(len(ctx.dicts), 4)