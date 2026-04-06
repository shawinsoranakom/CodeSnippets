def test_wait_output_timeout_children(self, kill_process_mock):
        self.proc_mock.wait.side_effect = TimeoutExpired(3)
        self.proc_mock.children.return_value = [Mock()] * 2
        assert not rerun._wait_output(Mock(), False)
        assert kill_process_mock.call_count == 3