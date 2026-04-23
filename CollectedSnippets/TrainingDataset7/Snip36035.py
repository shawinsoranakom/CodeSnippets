def test_no_exception(self):
        # Should raise no exception if _exception is None
        autoreload.raise_last_exception()