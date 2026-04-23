def test_runner_custom_defaults(self):
        self.cmd.default_addr = "0.0.0.0"
        self.cmd.default_port = "5000"
        call_command(self.cmd)
        self.assertServerSettings("0.0.0.0", "5000")