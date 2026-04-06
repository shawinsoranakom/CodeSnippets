def test_get_output_invalid_continuation_byte(self, popen_mock):
        output = b'ls: illegal option -- \xc3\nusage: ls [-@ABC...] [file ...]\n'
        expected = u'ls: illegal option -- \ufffd\nusage: ls [-@ABC...] [file ...]\n'
        popen_mock.return_value.stdout.read.return_value = output
        actual = rerun.get_output('', '')
        assert actual == expected