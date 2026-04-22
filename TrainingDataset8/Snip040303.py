def test_parse_url_path_404(self):
        responses = [
            self.fetch("/nonexistent"),
            self.fetch("/page2/nonexistent"),
            self.fetch(f"/page3/{self._filename}"),
        ]

        for r in responses:
            assert r.code == 404