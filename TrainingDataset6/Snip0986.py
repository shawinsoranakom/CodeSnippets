def test_wait_output_timeout(self, kill_process_mock):
        self.proc_mock.wait.side_effect = TimeoutExpired(3)
        self.proc_mock.children.return_value = []
        assert not rerun._wait_output(Mock(), False)
        kill_process_mock.assert_called_once_with(self.proc_mock)