def test_specified_port_bind(self):
        """LiveServerTestCase.port customizes the server's port."""
        TestCase = type("TestCase", (LiveServerBase,), {})
        # Find an open port and tell TestCase to use it.
        s = socket.socket()
        s.bind(("", 0))
        TestCase.port = s.getsockname()[1]
        s.close()
        TestCase._start_server_thread()
        try:
            self.assertEqual(
                TestCase.port,
                TestCase.server_thread.port,
                f"Did not use specified port for LiveServerTestCase thread: "
                f"{TestCase.port}",
            )
        finally:
            TestCase.doClassCleanups()