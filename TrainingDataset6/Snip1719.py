def os_environ_pathsep(monkeypatch, path, pathsep):
    env = {'PATH': path}
    monkeypatch.setattr('os.environ', env)
    monkeypatch.setattr('os.pathsep', pathsep)
    return env