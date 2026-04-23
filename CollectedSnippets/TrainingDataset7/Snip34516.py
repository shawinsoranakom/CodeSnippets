def test_unknown_block_tag(self):
        engine = self._engine()
        msg = (
            "Invalid block tag on line 1: 'foobar'. Did you forget to "
            "register or load this tag?"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            engine.from_string("lala{% foobar %}")