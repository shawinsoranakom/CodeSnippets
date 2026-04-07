def test_unpacks_ipv4(self):
        self.assertEqual(
            clean_ipv6_address("::ffff:0a0a:0a0a", unpack_ipv4=True), "10.10.10.10"
        )
        self.assertEqual(
            clean_ipv6_address("::ffff:1234:1234", unpack_ipv4=True), "18.52.18.52"
        )
        self.assertEqual(
            clean_ipv6_address("::ffff:18.52.18.52", unpack_ipv4=True), "18.52.18.52"
        )