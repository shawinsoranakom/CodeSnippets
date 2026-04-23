def test_tag_invalid(self):
        msg = "Unsupported arguments to Library.tag: (None, '')"
        with self.assertRaisesMessage(ValueError, msg):
            self.library.tag(None, "")