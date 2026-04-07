def test_namedendblocks04(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("namedendblocks04")