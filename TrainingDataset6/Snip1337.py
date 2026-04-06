def test_match(cmd):
    assert match(
        Command('heroku {}'.format(cmd), suggest_output))