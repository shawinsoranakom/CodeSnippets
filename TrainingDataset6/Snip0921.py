def set_shell(monkeypatch):
    def _set(cls):
        shell = cls()
        monkeypatch.setattr('thefuck.shells.shell', shell)
        return shell

    return _set