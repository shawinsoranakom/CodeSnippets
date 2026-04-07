def test_message_list(self):
        v = ValidationError(["First Problem", "Second Problem"])
        self.assertEqual(str(v), "['First Problem', 'Second Problem']")
        self.assertEqual(
            repr(v), "ValidationError(['First Problem', 'Second Problem'])"
        )