def captured_stderr():
    """Capture the output of sys.stderr:

    with captured_stderr() as stderr:
        print("hello", file=sys.stderr)
    self.assertEqual(stderr.getvalue(), "hello\n")
    """
    return captured_output("stderr")