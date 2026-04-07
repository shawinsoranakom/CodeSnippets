def test_runserver_addrport(self):
        call_command(self.cmd)
        self.assertServerSettings("127.0.0.1", "8000")

        call_command(self.cmd, addrport="1.2.3.4:8000")
        self.assertServerSettings("1.2.3.4", "8000")

        call_command(self.cmd, addrport="7000")
        self.assertServerSettings("127.0.0.1", "7000")