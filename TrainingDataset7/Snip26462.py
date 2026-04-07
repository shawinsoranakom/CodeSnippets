def test_ok(self):
        msg = "some message"
        self.request._messages = self.storage
        messages.add_message(self.request, messages.DEBUG, msg)
        [message] = self.storage.store
        self.assertEqual(msg, message.message)