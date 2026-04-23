def test_runner_hostname(self):
        call_command(self.cmd, addrport="localhost:8000")
        self.assertServerSettings("localhost", "8000")

        call_command(self.cmd, addrport="test.domain.local:7000")
        self.assertServerSettings("test.domain.local", "7000")