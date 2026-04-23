def _mock_subprocess_run(*args, **kwargs):
            handler = signal.getsignal(signal.SIGINT)
            self.assertEqual(handler, signal.SIG_IGN)