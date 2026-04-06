def test_wait_output_is_not_slow(self, settings):
        assert rerun._wait_output(Mock(), False)
        self.proc_mock.wait.assert_called_once_with(settings.wait_command)