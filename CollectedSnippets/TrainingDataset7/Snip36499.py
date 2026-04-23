def test_address_too_long(self):
        addresses = [
            "0000:0000:0000:0000:0000:ffff:192.168.100.228",  # IPv4-mapped IPv6 address
            "0000:0000:0000:0000:0000:ffff:192.168.100.228%123456",  # % scope/zone
            "fe80::223:6cff:fe8a:2e8a:1234:5678:00000",  # MAX_IPV6_ADDRESS_LENGTH + 1
        ]
        msg = "This is the error message."
        value_error_msg = "Unable to convert %s to an IPv6 address (value too long)."
        for addr in addresses:
            with self.subTest(addr=addr):
                self.assertGreater(len(addr), MAX_IPV6_ADDRESS_LENGTH)
                self.assertEqual(is_valid_ipv6_address(addr), False)
                with self.assertRaisesMessage(ValidationError, msg) as ctx:
                    clean_ipv6_address(addr, error_message=msg)
                exception_traceback = StringIO()
                traceback.print_exception(ctx.exception, file=exception_traceback)
                self.assertIn(value_error_msg % addr, exception_traceback.getvalue())