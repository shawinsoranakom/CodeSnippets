def test_exception_with_notes(self):
        request = self.rf.get("/test_view/")
        try:
            try:
                raise RuntimeError("Oops")
            except Exception as err:
                err.add_note("First Note")
                err.add_note("Second Note")
                err.add_note(mark_safe("<script>alert(1);</script>"))
                raise err
        except Exception:
            exc_type, exc_value, tb = sys.exc_info()

        reporter = ExceptionReporter(request, exc_type, exc_value, tb)
        html = reporter.get_traceback_html()
        self.assertIn(
            '<pre class="exception_value">Oops\nFirst Note\nSecond Note\n'
            "&lt;script&gt;alert(1);&lt;/script&gt;</pre>",
            html,
        )
        self.assertIn(
            "Exception Value: Oops\nFirst Note\nSecond Note\n"
            "&lt;script&gt;alert(1);&lt;/script&gt;",
            html,
        )

        text = reporter.get_traceback_text()
        self.assertIn(
            "Exception Value: Oops\nFirst Note\nSecond Note\n"
            "<script>alert(1);</script>",
            text,
        )