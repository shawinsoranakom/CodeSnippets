def os_path(monkeypatch):
    monkeypatch.setattr('os.path.isfile', lambda x: not x.startswith('-'))