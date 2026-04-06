def get_all_executables(mocker):
    mocker.patch(
        "thefuck.rules.wrong_hyphen_before_subcommand.get_all_executables",
        return_value=["git", "apt", "apt-get", "ls", "pwd"],
    )