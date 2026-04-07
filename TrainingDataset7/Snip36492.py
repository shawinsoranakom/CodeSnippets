def test_validates_correct_with_ipv6_instance(self):
        cases = [
            IPv6Address("::ffff:2.125.160.216"),
            IPv6Address("fe80::1"),
            IPv6Address("::"),
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertIs(is_valid_ipv6_address(case), True)