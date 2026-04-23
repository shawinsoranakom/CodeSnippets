def test_generic_ipaddress_max_length_custom(self):
        # Valid IPv4-mapped IPv6 address, len 45.
        addr = "0000:0000:0000:0000:0000:ffff:192.168.100.228"
        f = GenericIPAddressField(max_length=len(addr))
        f.clean(addr)