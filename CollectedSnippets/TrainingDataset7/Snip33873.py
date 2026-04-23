def test_namedendblocks03(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("namedendblocks03")