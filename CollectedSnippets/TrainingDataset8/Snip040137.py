def test_nonmatching_url_is_not_replaced(self):
        for url in INVALID_URLS:
            assert url == url_util.process_gitblob_url(url)