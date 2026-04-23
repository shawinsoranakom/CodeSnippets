def test_broken_partial_nesting(self):
        with self.assertRaises(TemplateSyntaxError) as cm:
            self.engine.get_template("partial_broken_nesting")

        self.assertIn("endpartialdef", str(cm.exception))
        self.assertIn("Invalid block tag", str(cm.exception))
        self.assertIn("'endpartialdef inner'", str(cm.exception))

        reporter = ExceptionReporter(None, cm.exception.__class__, cm.exception, None)
        traceback_data = reporter.get_traceback_data()

        exception_value = str(traceback_data.get("exception_value", ""))
        self.assertIn("Invalid block tag", exception_value)
        self.assertIn("'endpartialdef inner'", str(cm.exception))