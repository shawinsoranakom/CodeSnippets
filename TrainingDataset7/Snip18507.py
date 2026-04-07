def test_get_sequences(self):
        msg = self.may_require_msg % "get_sequences"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.introspection.get_sequences(None, None)