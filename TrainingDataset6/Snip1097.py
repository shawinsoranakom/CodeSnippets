def test_match(zip_error, script, filename):
    zip_error(filename)
    assert match(Command(script, ''))