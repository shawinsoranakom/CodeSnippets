def captured_stdin():
    """Capture the input to sys.stdin:

    with captured_stdin() as stdin:
        stdin.write('hello\n')
        stdin.seek(0)
        # call test code that consumes from sys.stdin
        captured = input()
    self.assertEqual(captured, "hello")
    """
    return captured_output("stdin")