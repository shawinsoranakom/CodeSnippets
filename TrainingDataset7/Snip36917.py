def test_local_variable_escaping(self):
        """Safe strings in local variables are escaped."""
        try:
            local = mark_safe("<p>Local variable</p>")
            raise ValueError(local)
        except Exception:
            exc_type, exc_value, tb = sys.exc_info()
        html = ExceptionReporter(None, exc_type, exc_value, tb).get_traceback_html()
        self.assertIn(
            '<td class="code"><pre>&#x27;&lt;p&gt;Local variable&lt;/p&gt;&#x27;</pre>'
            "</td>",
            html,
        )