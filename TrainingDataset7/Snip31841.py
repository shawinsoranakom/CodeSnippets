def test_port_bind(self):
        """
        Each LiveServerTestCase binds to a unique port or fails to start a
        server thread when run concurrently (#26011).
        """
        TestCase = type("TestCase", (LiveServerBase,), {})
        try:
            TestCase._start_server_thread()
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                # We're out of ports, LiveServerTestCase correctly fails with
                # an OSError.
                return
            # Unexpected error.
            raise
        try:
            self.assertNotEqual(
                self.live_server_url,
                TestCase.live_server_url,
                f"Acquired duplicate server addresses for server threads: "
                f"{self.live_server_url}",
            )
        finally:
            TestCase.doClassCleanups()