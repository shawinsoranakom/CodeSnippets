def test_custom_end_tag(self):
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string(
            "{% load custom %}{% div_custom_end %}{{ name }}{% divend %}"
        )
        self.assertEqual(t.render(c), "<div>Jack &amp; Jill</div>")

        with self.assertRaisesMessage(
            TemplateSyntaxError,
            "'enddiv_custom_end', expected 'divend'. Did you forget to register or "
            "load this tag?",
        ):
            self.engine.from_string(
                "{% load custom %}{% div_custom_end %}{{ name }}{% enddiv_custom_end %}"
            )