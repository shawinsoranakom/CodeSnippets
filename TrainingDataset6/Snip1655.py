def test_git_support(called, command, output):
    @git_support
    def fn(command):
        return command.script

    assert fn(Command(called, output)) == command