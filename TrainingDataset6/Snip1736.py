def key(self, monkeypatch):
        monkeypatch.setattr('thefuck.utils.Cache._get_key',
                            lambda *_: 'key')
        return 'key'