def test_verbatim_tag04(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("verbatim-tag04")