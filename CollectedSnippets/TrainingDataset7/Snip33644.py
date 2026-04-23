def test_unpack_single_quote(self):
        msg = """'for' tag received an invalid argument: for 'k' in items"""
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("single-quote", {"items": (1, 2)})