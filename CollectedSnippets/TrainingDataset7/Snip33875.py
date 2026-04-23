def test_namedendblocks05(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("namedendblocks05")