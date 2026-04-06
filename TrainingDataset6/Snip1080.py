def test_get_new_command(composer_not_command, composer_not_command_one_of_this, composer_require_instead_of_install):
    assert (get_new_command(Command('composer udpate',
                                    composer_not_command))
            == 'composer update')
    assert (get_new_command(Command('composer pdate',
                                    composer_not_command_one_of_this))
            == 'composer selfupdate')
    assert (get_new_command(Command('composer install package',
                                    composer_require_instead_of_install))
            == 'composer require package')