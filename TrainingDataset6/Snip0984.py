def test_wait_output_is_slow(self, settings):
        assert rerun._wait_output(Mock(), True)
        self.proc_mock.wait.assert_called_once_with(settings.wait_slow_command)