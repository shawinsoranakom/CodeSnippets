def test_get_valid_filename(self):
        filename = "^&'@{}[],$=!-#()%+~_123.txt"
        self.assertEqual(text.get_valid_filename(filename), "-_123.txt")
        self.assertEqual(text.get_valid_filename(lazystr(filename)), "-_123.txt")
        msg = "Could not derive file name from '???'"
        with self.assertRaisesMessage(SuspiciousFileOperation, msg):
            text.get_valid_filename("???")
        # After sanitizing this would yield '..'.
        msg = "Could not derive file name from '$.$.$'"
        with self.assertRaisesMessage(SuspiciousFileOperation, msg):
            text.get_valid_filename("$.$.$")