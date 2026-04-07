def test_generic_ipaddress_max_length_validation_error(self):
        # Valid IPv4-mapped IPv6 address, len 45.
        addr = "0000:0000:0000:0000:0000:ffff:192.168.100.228"

        cases = [
            ({}, MAX_IPV6_ADDRESS_LENGTH),  # Default value.
            ({"max_length": len(addr) - 1}, len(addr) - 1),
        ]
        for kwargs, max_length in cases:
            max_length_plus_one = max_length + 1
            msg = (
                f"Ensure this value has at most {max_length} characters (it has "
                f"{max_length_plus_one}).'"
            )
            with self.subTest(max_length=max_length):
                f = GenericIPAddressField(**kwargs)
                with self.assertRaisesMessage(ValidationError, msg):
                    f.clean("x" * max_length_plus_one)
                with self.assertRaisesMessage(
                    ValidationError, "This is not a valid IPv6 address."
                ):
                    f.clean(addr)