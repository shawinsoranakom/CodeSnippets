def test_load_dotenv(monkeypatch):
    # can't use monkeypatch.delitem since the keys don't exist yet
    for item in ("FOO", "BAR", "SPAM", "HAM"):
        monkeypatch._setitem.append((os.environ, item, notset))

    monkeypatch.setenv("EGGS", "3")
    monkeypatch.chdir(test_path)
    assert load_dotenv()
    assert Path.cwd() == test_path
    # .flaskenv doesn't overwrite .env
    assert os.environ["FOO"] == "env"
    # set only in .flaskenv
    assert os.environ["BAR"] == "bar"
    # set only in .env
    assert os.environ["SPAM"] == "1"
    # set manually, files don't overwrite
    assert os.environ["EGGS"] == "3"
    # test env file encoding
    assert os.environ["HAM"] == "火腿"
    # Non existent file should not load
    assert not load_dotenv("non-existent-file", load_defaults=False)