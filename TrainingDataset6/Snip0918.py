def no_cache(monkeypatch):
    monkeypatch.setattr('thefuck.utils.cache.disabled', True)