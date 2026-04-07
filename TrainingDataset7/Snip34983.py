def test_log(self):
        custom_low_level = 5
        custom_high_level = 45
        msg = "logging message"
        cases = [
            (0, None, False),
            (0, custom_low_level, False),
            (0, logging.DEBUG, False),
            (0, logging.INFO, False),
            (0, logging.WARNING, False),
            (0, custom_high_level, False),
            (1, None, True),
            (1, custom_low_level, False),
            (1, logging.DEBUG, False),
            (1, logging.INFO, True),
            (1, logging.WARNING, True),
            (1, custom_high_level, True),
            (2, None, True),
            (2, custom_low_level, True),
            (2, logging.DEBUG, True),
            (2, logging.INFO, True),
            (2, logging.WARNING, True),
            (2, custom_high_level, True),
            (3, None, True),
            (3, custom_low_level, True),
            (3, logging.DEBUG, True),
            (3, logging.INFO, True),
            (3, logging.WARNING, True),
            (3, custom_high_level, True),
        ]
        for verbosity, level, output in cases:
            with self.subTest(verbosity=verbosity, level=level):
                with captured_stdout() as stdout:
                    runner = DiscoverRunner(verbosity=verbosity)
                    runner.log(msg, level)
                    self.assertEqual(stdout.getvalue(), f"{msg}\n" if output else "")