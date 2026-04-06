def test_get_new_command():
    assert get_new_command(Command('./manage.py migrate auth', ''))\
        == './manage.py migrate auth --delete-ghost-migrations'