def test_no_escalation(self):
        self.mock_popen_res.stdout.read.side_effect = [b"my_stdout\n", b"second_line"]
        self.mock_popen_res.stderr.read.side_effect = [b"my_stderr"]
        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            []]
        self.mock_selector.get_map.side_effect = lambda: True

        return_code, b_stdout, b_stderr = self.conn._run("ssh", "this is input data")
        assert return_code == 0
        assert b_stdout == b'my_stdout\nsecond_line'
        assert b_stderr == b'my_stderr'
        assert self.mock_selector.register.called is True
        assert self.mock_selector.register.call_count == 2
        assert self.conn._send_initial_data.called is True
        assert self.conn._send_initial_data.call_count == 1
        assert self.conn._send_initial_data.call_args[0][1] == 'this is input data'