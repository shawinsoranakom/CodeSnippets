def test_github_url_is_replaced(self):
        for (target, processed) in GITHUB_URLS:
            assert url_util.process_gitblob_url(target) == processed