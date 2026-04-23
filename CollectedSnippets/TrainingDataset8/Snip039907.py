def test_reload_secrets(self, _):
        """Re-parsing the secrets file is thread-safe."""

        def reload_secrets(_: int) -> None:
            # Reset secrets, and then access a secret to reparse.
            self.secrets._reset()
            self.assertEqual(self.secrets["db_username"], "Jane")

        call_on_threads(reload_secrets, num_threads=self.NUM_THREADS)