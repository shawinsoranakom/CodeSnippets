def test_simple_tag_invalid(self):
        msg = "Invalid arguments provided to simple_tag"
        with self.assertRaisesMessage(ValueError, msg):
            self.library.simple_tag("invalid")