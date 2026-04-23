def test_gist_url_is_replaced(self):
        for (target, processed) in GIST_URLS:
            assert url_util.process_gitblob_url(target) == processed