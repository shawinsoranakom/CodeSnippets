def test_reactorless_datauri(self):
        log = self.run_script("reactorless_datauri.py")
        assert "Not using a Twisted reactor" in log
        assert "Spider closed (finished)" in log
        assert "{'data': 'foo'}" in log
        assert "'item_scraped_count': 1" in log
        assert "ERROR: " not in log
        assert log.count("WARNING: HttpxDownloadHandler is experimental") == 2
        assert log.count("WARNING: ") == 2