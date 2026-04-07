def test_simpletag_renamed03(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("simpletag-renamed03")