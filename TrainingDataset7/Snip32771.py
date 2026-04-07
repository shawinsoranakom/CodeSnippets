def test_exception_debug_info_min_context(self):
        with self.assertRaises(TemplateSyntaxError) as e:
            self.engine.get_template("template_backends/syntax_error.html")
        debug = e.exception.template_debug
        self.assertEqual(debug["after"], "")
        self.assertEqual(debug["before"], "")
        self.assertEqual(debug["during"], "{% block %}")
        self.assertEqual(debug["bottom"], 1)
        self.assertEqual(debug["top"], 0)
        self.assertEqual(debug["line"], 1)
        self.assertEqual(debug["total"], 1)
        self.assertEqual(len(debug["source_lines"]), 1)
        self.assertTrue(debug["name"].endswith("syntax_error.html"))
        self.assertIn("message", debug)