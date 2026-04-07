def test_template_name_not_in_debug_view(self):
        try:
            Template("{% endfor %}", origin=Origin("test.html"))
        except TemplateSyntaxError as e:
            reporter = ExceptionReporter(None, e.__class__, e, None)
            traceback_data = reporter.get_traceback_data()
            self.assertEqual(traceback_data["exception_value"], self.template_error_msg)