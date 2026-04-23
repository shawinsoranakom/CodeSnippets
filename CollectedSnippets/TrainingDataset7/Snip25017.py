def test_add_location_file(self):
        """makemessages --add-location=file"""
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, add_location="file"
        )
        self.assertTrue(os.path.exists(self.PO_FILE))
        # Comment with source file relative path is present.
        self.assertLocationCommentPresent(self.PO_FILE, None, "templates", "test.html")
        # But it should not contain the line number.
        self.assertLocationCommentNotPresent(
            self.PO_FILE, "Translatable literal #6b", "templates", "test.html"
        )