def test_15070_use_l10n(self):
        """
        Inclusion tag passes down `use_l10n` of context to the
        Context of the included/rendered template as well.
        """
        c = Context({})
        t = self.engine.from_string("{% load inclusion %}{% inclusion_tag_use_l10n %}")
        self.assertEqual(t.render(c).strip(), "None")

        c.use_l10n = True
        self.assertEqual(t.render(c).strip(), "True")