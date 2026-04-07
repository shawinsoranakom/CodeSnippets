def test_super_errors(self):
        """
        #18169 -- NoReverseMatch should not be silence in block.super.
        """
        engine = self._engine(app_dirs=True)
        t = engine.get_template("included_content.html")
        with self.assertRaises(NoReverseMatch):
            t.render(Context())