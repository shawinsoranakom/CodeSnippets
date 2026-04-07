def test_exception_debug_info_max_context(self):
        with self.assertRaises(TemplateSyntaxError) as e:
            self.engine.get_template("template_backends/syntax_error2.html")
        debug = e.exception.template_debug
        self.assertEqual(debug["after"], "")
        self.assertEqual(debug["before"], "")
        self.assertEqual(debug["during"], "{% block %}")
        self.assertEqual(debug["bottom"], 26)
        self.assertEqual(debug["top"], 5)
        self.assertEqual(debug["line"], 16)
        self.assertEqual(debug["total"], 31)
        self.assertEqual(len(debug["source_lines"]), 21)
        self.assertTrue(debug["name"].endswith("syntax_error2.html"))
        self.assertIn("message", debug)