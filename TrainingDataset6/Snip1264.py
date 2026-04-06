def test_not_match():
    script = "git push -u origin master"
    assert not match(Command(script, "Everything up-to-date"))