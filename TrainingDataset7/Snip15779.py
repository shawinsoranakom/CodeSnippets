def assertServerSettings(self, addr, port, ipv6=False, raw_ipv6=False):
        self.assertEqual(self.cmd.addr, addr)
        self.assertEqual(self.cmd.port, port)
        self.assertEqual(self.cmd.use_ipv6, ipv6)
        self.assertEqual(self.cmd._raw_ipv6, raw_ipv6)