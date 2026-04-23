def test_namedendblocks02(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("namedendblocks02")