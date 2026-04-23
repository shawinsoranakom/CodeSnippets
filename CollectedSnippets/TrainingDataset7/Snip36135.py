def test_constant_time_compare(self):
        # It's hard to test for constant time, just test the result.
        self.assertTrue(constant_time_compare(b"spam", b"spam"))
        self.assertFalse(constant_time_compare(b"spam", b"eggs"))
        self.assertTrue(constant_time_compare("spam", "spam"))
        self.assertFalse(constant_time_compare("spam", "eggs"))
        self.assertTrue(constant_time_compare(b"spam", "spam"))
        self.assertFalse(constant_time_compare("spam", b"eggs"))
        self.assertTrue(constant_time_compare("ありがとう", "ありがとう"))
        self.assertFalse(constant_time_compare("ありがとう", "おはよう"))