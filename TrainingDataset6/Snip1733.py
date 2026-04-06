def enable_cache(self, monkeypatch, shelve):
        monkeypatch.setattr('thefuck.utils.cache.disabled', False)
        _cache._init_db()