def test_access_secrets(self, _):
        """Accessing secrets is thread-safe."""

        def access_secrets(_: int) -> None:
            self.assertEqual(self.secrets["db_username"], "Jane")
            self.assertEqual(self.secrets["subsection"]["email"], "eng@streamlit.io")
            self.assertEqual(self.secrets["subsection"].email, "eng@streamlit.io")

        call_on_threads(access_secrets, num_threads=self.NUM_THREADS)