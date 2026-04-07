def test_now_template_tag_uses_current_time_zone(self):
        # Regression for #17343
        tpl = Template('{% now "O" %}')
        self.assertEqual(tpl.render(Context({})), "+0300")
        with timezone.override(ICT):
            self.assertEqual(tpl.render(Context({})), "+0700")