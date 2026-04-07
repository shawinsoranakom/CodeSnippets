def test_no_location_enabled(self):
        """
        Behavior is correct if --no-location switch is specified. See #16903.
        """
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, no_location=True
        )
        self.assertTrue(os.path.exists(self.PO_FILE))
        self.assertLocationCommentNotPresent(self.PO_FILE, None, "test.html")