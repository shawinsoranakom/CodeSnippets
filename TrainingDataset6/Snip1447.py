def test_get_new_command():
    assert get_new_command(Command('pip install -r requirements.txt', '')) == 'pip install --user -r requirements.txt'
    assert get_new_command(Command('pip install bacon', '')) == 'pip install --user bacon'
    assert get_new_command(Command('pip install --user -r requirements.txt', '')) == 'sudo pip install -r requirements.txt'