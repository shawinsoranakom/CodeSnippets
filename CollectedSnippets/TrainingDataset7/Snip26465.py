def test_middleware_missing_silently(self):
        messages.add_message(
            self.request, messages.DEBUG, "some message", fail_silently=True
        )
        self.assertEqual(self.storage.store, [])