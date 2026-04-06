def test_get_new_command():
    script = "git push -u origin master"
    output = "error: src refspec master does not match any\nerror: failed to..."
    new_command = 'git commit -m "Initial commit" && git push -u origin master'
    assert get_new_command(Command(script, output)) == new_command