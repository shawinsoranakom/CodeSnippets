def test_runner_addrport_ipv6(self):
        call_command(self.cmd, addrport="", use_ipv6=True)
        self.assertServerSettings("::1", "8000", ipv6=True, raw_ipv6=True)

        call_command(self.cmd, addrport="7000", use_ipv6=True)
        self.assertServerSettings("::1", "7000", ipv6=True, raw_ipv6=True)

        call_command(self.cmd, addrport="[2001:0db8:1234:5678::9]:7000")
        self.assertServerSettings(
            "2001:0db8:1234:5678::9", "7000", ipv6=True, raw_ipv6=True
        )