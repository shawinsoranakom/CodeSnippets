def test_protocol(self):
        """Launched server serves with HTTP 1.1."""
        with self.urlopen("/example_view/") as f:
            self.assertEqual(f.version, 11)