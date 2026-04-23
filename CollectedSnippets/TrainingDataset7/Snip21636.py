def test_when_rejects_invalid_arguments(self):
        msg = "The following kwargs are invalid: '_connector', '_negated'"
        with self.assertRaisesMessage(TypeError, msg):
            When(_negated=True, _connector="evil")