def which(mocker):
    return mocker.patch('thefuck.rules.sudo_command_from_user_path.which',
                        return_value='/usr/bin/app')