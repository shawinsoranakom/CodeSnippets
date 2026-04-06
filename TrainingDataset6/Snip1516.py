def test_get_new_command():
    assert get_new_command(Command('systemctl nginx start', '')) == "systemctl start nginx"
    assert get_new_command(Command('sudo systemctl nginx start', '')) == "sudo systemctl start nginx"