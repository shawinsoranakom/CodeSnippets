def test_named_handlers(self):
        for code in [400, 403, 404, 500]:
            with self.subTest(code=code):
                self.assertEqual(self.resolver.resolve_error_handler(code), empty_view)