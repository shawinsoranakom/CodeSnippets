def test_no_location_disabled(self):
        """Behavior is correct if --no-location switch isn't specified."""
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, no_location=False
        )
        self.assertTrue(os.path.exists(self.PO_FILE))
        # #16903 -- Standard comment with source file relative path should be
        # present
        self.assertLocationCommentPresent(
            self.PO_FILE, "Translatable literal #6b", "templates", "test.html"
        )