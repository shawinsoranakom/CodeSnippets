def test_get_output(self, popen_mock, wait_output_mock):
        popen_mock.return_value.stdout.read.return_value = b'output'
        assert rerun.get_output('', '') is None
        wait_output_mock.assert_called_once()