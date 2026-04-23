def test_compile_tag_error(self):
        """
        Errors raised while compiling nodes should include the token
        information.
        """
        engine = self._engine(
            libraries={"bad_tag": "template_tests.templatetags.bad_tag"},
        )
        with self.assertRaises(RuntimeError) as e:
            engine.from_string("{% load bad_tag %}{% badtag %}")
        if self.debug_engine:
            self.assertEqual(e.exception.template_debug["during"], "{% badtag %}")