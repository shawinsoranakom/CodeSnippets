def test_add_remove_invalid_type(self):
        msg = "Field 'id' expected a number but got 'invalid'."
        for method in ["add", "remove"]:
            with self.subTest(method), self.assertRaisesMessage(ValueError, msg):
                getattr(self.a1.publications, method)("invalid")