def test_add_location_never(self):
        """makemessages --add-location=never"""
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, add_location="never"
        )
        self.assertTrue(os.path.exists(self.PO_FILE))
        self.assertLocationCommentNotPresent(self.PO_FILE, None, "test.html")