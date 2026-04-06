def test_git_support_match(command, is_git, output):
    @git_support
    def fn(command):
        return True

    assert fn(Command(command, output)) == is_git