def test_fixtures_loaded(self):
        """
        Fixtures are properly loaded and visible to the live server thread.
        """
        with self.urlopen("/model_view/") as f:
            self.assertCountEqual(f.read().splitlines(), [b"jane", b"robert"])