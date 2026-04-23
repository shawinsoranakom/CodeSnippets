def test_cleans_with_v4_mapping(self):
        self.assertEqual(clean_ipv6_address("::ffff:0a0a:0a0a"), "::ffff:10.10.10.10")
        self.assertEqual(clean_ipv6_address("::ffff:1234:1234"), "::ffff:18.52.18.52")
        self.assertEqual(clean_ipv6_address("::ffff:18.52.18.52"), "::ffff:18.52.18.52")
        self.assertEqual(clean_ipv6_address("::ffff:0.52.18.52"), "::ffff:0.52.18.52")
        self.assertEqual(clean_ipv6_address("::ffff:0.0.0.0"), "::ffff:0.0.0.0")