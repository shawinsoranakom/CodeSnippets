def setup_method(self, test_method):
        self.patcher = patch('thefuck.output_readers.rerun.Process')
        process_mock = self.patcher.start()
        self.proc_mock = process_mock.return_value = Mock()