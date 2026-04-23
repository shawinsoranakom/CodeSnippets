def test_cleans_plain_address(self):
        self.assertEqual(clean_ipv6_address("DEAD::0:BEEF"), "dead::beef")
        self.assertEqual(
            clean_ipv6_address("2001:000:a:0000:0:fe:fe:beef"), "2001:0:a::fe:fe:beef"
        )
        self.assertEqual(
            clean_ipv6_address("2001::a:0000:0:fe:fe:beef"), "2001:0:a::fe:fe:beef"
        )