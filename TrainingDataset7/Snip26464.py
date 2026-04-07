def test_middleware_missing(self):
        msg = (
            "You cannot add messages without installing "
            "django.contrib.messages.middleware.MessageMiddleware"
        )
        with self.assertRaisesMessage(messages.MessageFailure, msg):
            messages.add_message(self.request, messages.DEBUG, "some message")
        self.assertEqual(self.storage.store, [])