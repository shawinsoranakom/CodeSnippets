def test_sudo_support(return_value, command, called, result):
    def fn(command):
        assert command == Command(called, '')
        return return_value

    assert sudo_support(fn)(Command(command, '')) == result