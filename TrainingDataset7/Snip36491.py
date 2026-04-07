def test_validates_correct_with_v4mapping(self):
        self.assertTrue(is_valid_ipv6_address("::ffff:254.42.16.14"))
        self.assertTrue(is_valid_ipv6_address("::ffff:0a0a:0a0a"))