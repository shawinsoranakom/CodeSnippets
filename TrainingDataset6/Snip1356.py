def test_get_new_command(is_not_task):
    assert (get_new_command(Command('lein rpl --help', is_not_task))
            == ['lein repl --help', 'lein jar --help'])