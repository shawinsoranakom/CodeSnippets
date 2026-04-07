def test_broken_partial_unclosed_exception_info(self):
        with self.assertRaises(TemplateSyntaxError) as cm:
            self.engine.get_template("partial_broken_unclosed")

        self.assertIn("endpartialdef", str(cm.exception))
        self.assertIn("Unclosed tag", str(cm.exception))

        reporter = ExceptionReporter(None, cm.exception.__class__, cm.exception, None)
        traceback_data = reporter.get_traceback_data()

        exception_value = str(traceback_data.get("exception_value", ""))
        self.assertIn("Unclosed tag", exception_value)