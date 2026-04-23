def test_generic_ipaddress_as_ipv6_only(self):
        f = GenericIPAddressField(protocol="IPv6")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv6 address.'"):
            f.clean("127.0.0.1")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv6 address.'"):
            f.clean("foo")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv6 address.'"):
            f.clean("127.0.0.")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv6 address.'"):
            f.clean("1.2.3.4.5")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid IPv6 address.'"):
            f.clean("256.125.1.5")
        self.assertEqual(
            f.clean(" fe80::223:6cff:fe8a:2e8a "), "fe80::223:6cff:fe8a:2e8a"
        )
        self.assertEqual(
            f.clean(" 2a02::223:6cff:fe8a:2e8a "), "2a02::223:6cff:fe8a:2e8a"
        )
        with self.assertRaisesMessage(
            ValidationError, "'This is not a valid IPv6 address.'"
        ):
            f.clean("12345:2:3:4")
        with self.assertRaisesMessage(
            ValidationError, "'This is not a valid IPv6 address.'"
        ):
            f.clean("1::2:3::4")
        with self.assertRaisesMessage(
            ValidationError, "'This is not a valid IPv6 address.'"
        ):
            f.clean("foo::223:6cff:fe8a:2e8a")
        with self.assertRaisesMessage(
            ValidationError, "'This is not a valid IPv6 address.'"
        ):
            f.clean("1::2:3:4:5:6:7:8")
        with self.assertRaisesMessage(
            ValidationError, "'This is not a valid IPv6 address.'"
        ):
            f.clean("1:2")