def test_validates_incorrect_with_v4mapping(self):
        self.assertFalse(is_valid_ipv6_address("::ffff:999.42.16.14"))
        self.assertFalse(is_valid_ipv6_address("::ffff:zzzz:0a0a"))
        # The ::1.2.3.4 format used to be valid but was deprecated
        # in RFC 4291 section 2.5.5.1.
        self.assertTrue(is_valid_ipv6_address("::254.42.16.14"))
        self.assertTrue(is_valid_ipv6_address("::0a0a:0a0a"))
        self.assertFalse(is_valid_ipv6_address("::999.42.16.14"))
        self.assertFalse(is_valid_ipv6_address("::zzzz:0a0a"))