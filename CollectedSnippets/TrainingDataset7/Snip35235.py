def test_not_used(self):
        with self.assertTemplateNotUsed("template_used/base.html"):
            pass
        with self.assertTemplateNotUsed("template_used/alternative.html"):
            pass