def test_validates_incorrect_with_non_string(self):
        cases = [None, [], {}, (), Decimal("2.46"), 192.168, 42]
        for case in cases:
            with self.subTest(case=case):
                self.assertIs(is_valid_ipv6_address(case), False)