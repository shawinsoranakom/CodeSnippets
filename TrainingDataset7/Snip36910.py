def test_highlight_error_position(self):
        request = self.rf.get("/test_view/")
        try:
            try:
                raise AttributeError("Top level")
            except AttributeError as explicit:
                try:
                    raise ValueError(mark_safe("<p>2nd exception</p>")) from explicit
                except ValueError:
                    raise IndexError("Final exception")
        except Exception:
            exc_type, exc_value, tb = sys.exc_info()

        reporter = ExceptionReporter(request, exc_type, exc_value, tb)
        html = reporter.get_traceback_html()
        self.assertIn(
            "<pre>                raise AttributeError(&quot;Top level&quot;)\n"
            "                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^</pre>",
            html,
        )
        self.assertIn(
            "<pre>                    raise ValueError(mark_safe("
            "&quot;&lt;p&gt;2nd exception&lt;/p&gt;&quot;)) from explicit\n"
            "                         "
            "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^</pre>",
            html,
        )
        self.assertIn(
            "<pre>                    raise IndexError(&quot;Final exception&quot;)\n"
            "                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^</pre>",
            html,
        )
        # Pastebin.
        self.assertIn(
            "    raise AttributeError(&quot;Top level&quot;)\n"
            "    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
            html,
        )
        self.assertIn(
            "    raise ValueError(mark_safe("
            "&quot;&lt;p&gt;2nd exception&lt;/p&gt;&quot;)) from explicit\n"
            "    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
            html,
        )
        self.assertIn(
            "    raise IndexError(&quot;Final exception&quot;)\n"
            "    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
            html,
        )
        # Text traceback.
        text = reporter.get_traceback_text()
        self.assertIn(
            '    raise AttributeError("Top level")\n'
            "    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
            text,
        )
        self.assertIn(
            '    raise ValueError(mark_safe("<p>2nd exception</p>")) from explicit\n'
            "    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
            text,
        )
        self.assertIn(
            '    raise IndexError("Final exception")\n'
            "    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n",
            text,
        )