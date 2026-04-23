def test_too_large_values_handling(self):
        "Large values should not create a large HTML."
        large = 256 * 1024
        repr_of_str_adds = len(repr(""))
        try:

            class LargeOutput:
                def __repr__(self):
                    return repr("A" * large)

            largevalue = LargeOutput()  # NOQA
            raise ValueError()
        except Exception:
            exc_type, exc_value, tb = sys.exc_info()
        reporter = ExceptionReporter(None, exc_type, exc_value, tb)
        html = reporter.get_traceback_html()
        self.assertEqual(len(html) // 1024 // 128, 0)  # still fit in 128Kb
        self.assertIn(
            "&lt;trimmed %d bytes string&gt;" % (large + repr_of_str_adds,), html
        )