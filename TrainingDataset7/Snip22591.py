def test_generic_ipaddress_as_ipv4_only(self):
        f = GenericIPAddressField(protocol="IPv4")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        self.assertEqual(f.clean(" 127.0.0.1 "), "127.0.0.1")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv4 address.'"):
            f.clean("foo")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv4 address.'"):
            f.clean("127.0.0.")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv4 address.'"):
            f.clean("1.2.3.4.5")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv4 address.'"):
            f.clean("256.125.1.5")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv4 address.'"):
            f.clean("fe80::223:6cff:fe8a:2e8a")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv4 address.'"):
            f.clean("2a02::223:6cff:fe8a:2e8a")