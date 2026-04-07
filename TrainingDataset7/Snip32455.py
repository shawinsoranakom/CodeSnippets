def mock_input(stdout):
        def _input(msg):
            stdout.write(msg)
            return "yes"

        return _input