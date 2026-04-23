def test_password_with_become(self):
        # test with some become settings
        self.pc.prompt = b'Password:'
        self.conn.become.prompt = b'Password:'
        self.pc.become = True
        self.pc.success_key = 'BECOME-SUCCESS-abcdefg'
        self.conn.become._id = 'abcdefg'
        self.conn._examine_output.side_effect = self._password_with_prompt_examine_output
        self.mock_popen_res.stdout.read.side_effect = [b"Password:", b"BECOME-SUCCESS-abcdefg", b"abc"]
        self.mock_popen_res.stderr.read.side_effect = [b"123"]
        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            []]
        self.mock_selector.get_map.side_effect = lambda: True

        return_code, b_stdout, b_stderr = self.conn._run("ssh", "this is input data")
        self.mock_popen_res.stdin.flush.assert_called_once_with()
        assert return_code == 0
        assert b_stdout == b'abc'
        assert b_stderr == b'123'
        assert self.mock_selector.register.called is True
        assert self.mock_selector.register.call_count == 2
        assert self.conn._send_initial_data.called is True
        assert self.conn._send_initial_data.call_count == 1
        assert self.conn._send_initial_data.call_args[0][1] == 'this is input data'