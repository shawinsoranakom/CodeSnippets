def test_runner_ambiguous(self):
        # Only 4 characters, all of which could be in an ipv6 address
        call_command(self.cmd, addrport="beef:7654")
        self.assertServerSettings("beef", "7654")

        # Uses only characters that could be in an ipv6 address
        call_command(self.cmd, addrport="deadbeef:7654")
        self.assertServerSettings("deadbeef", "7654")