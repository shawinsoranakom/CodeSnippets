def test_runner_custom_defaults_ipv6(self):
        self.cmd.default_addr_ipv6 = "::"
        call_command(self.cmd, use_ipv6=True)
        self.assertServerSettings("::", "8000", ipv6=True, raw_ipv6=True)