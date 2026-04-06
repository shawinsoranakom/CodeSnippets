def test_get_new_command_with_settings(mocker, monkeypatch, test, settings):
    mocker.patch('os.path.isfile', return_value=True)
    monkeypatch.setenv('EDITOR', 'dummy_editor')

    cmd = Command(test.script, test.output)
    settings.fixcolcmd = '{editor} {file} +{line}:{col}'

    if test.col:
        assert (get_new_command(cmd) ==
                u'dummy_editor {} +{}:{} && {}'.format(test.file, test.line, test.col, test.script))
    else:
        assert (get_new_command(cmd) ==
                u'dummy_editor {} +{} && {}'.format(test.file, test.line, test.script))