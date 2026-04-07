def test_generic_ipaddress_normalization(self):
        # Test the normalizing code
        f = GenericIPAddressField()
        self.assertEqual(f.clean(" ::ffff:0a0a:0a0a  "), "::ffff:10.10.10.10")
        self.assertEqual(f.clean(" ::ffff:10.10.10.10  "), "::ffff:10.10.10.10")
        self.assertEqual(
            f.clean(" 2001:000:a:0000:0:fe:fe:beef  "), "2001:0:a::fe:fe:beef"
        )
        self.assertEqual(
            f.clean(" 2001::a:0000:0:fe:fe:beef  "), "2001:0:a::fe:fe:beef"
        )

        f = GenericIPAddressField(unpack_ipv4=True)
        self.assertEqual(f.clean(" ::ffff:0a0a:0a0a"), "10.10.10.10")