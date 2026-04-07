def test_add_location_full(self):
        """makemessages --add-location=full"""
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, add_location="full"
        )
        self.assertTrue(os.path.exists(self.PO_FILE))
        # Comment with source file relative path and line number is present.
        self.assertLocationCommentPresent(
            self.PO_FILE, "Translatable literal #6b", "templates", "test.html"
        )