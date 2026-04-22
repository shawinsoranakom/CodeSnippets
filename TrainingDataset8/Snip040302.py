def test_parse_url_path_200(self):
        responses = [
            self.fetch("/"),
            self.fetch(f"/{self._filename}"),
            self.fetch("/page1/"),
            self.fetch(f"/page1/{self._filename}"),
            self.fetch("/page2/"),
            self.fetch(f"/page2/{self._filename}"),
        ]

        for r in responses:
            assert r.code == 200