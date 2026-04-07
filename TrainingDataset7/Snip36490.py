def test_validates_correct_plain_address(self):
        self.assertTrue(is_valid_ipv6_address("fe80::223:6cff:fe8a:2e8a"))
        self.assertTrue(is_valid_ipv6_address("2a02::223:6cff:fe8a:2e8a"))
        self.assertTrue(is_valid_ipv6_address("1::2:3:4:5:6:7"))
        self.assertTrue(is_valid_ipv6_address("::"))
        self.assertTrue(is_valid_ipv6_address("::a"))
        self.assertTrue(is_valid_ipv6_address("2::"))