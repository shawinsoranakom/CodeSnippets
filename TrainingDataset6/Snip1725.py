def test_for_app(script, names, result):
    @for_app(*names)
    def match(command):
        return True

    assert match(Command(script, '')) == result