def test_no_password(self):
        expected = "<p><strong>No password set.</strong></p>"
        for value in ["", None, make_password(None)]:
            with self.subTest(value=value):
                self.assertEqual(render_password_as_hash(value), expected)