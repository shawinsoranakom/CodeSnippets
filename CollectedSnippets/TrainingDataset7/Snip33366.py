def test_template_tags_pgettext(self):
        """{% translate %} takes message contexts into account (#14806)."""
        trans_real._active = Local()
        trans_real._translations = {}
        with translation.override("de"):
            # Nonexistent context...
            t = self.get_template(
                '{% load i18n %}{% translate "May" context "nonexistent" %}'
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "May")

            # Existing context... using a literal
            t = self.get_template(
                '{% load i18n %}{% translate "May" context "month name" %}'
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "Mai")
            t = self.get_template('{% load i18n %}{% translate "May" context "verb" %}')
            rendered = t.render(Context())
            self.assertEqual(rendered, "Kann")

            # Using a variable
            t = self.get_template(
                '{% load i18n %}{% translate "May" context message_context %}'
            )
            rendered = t.render(Context({"message_context": "month name"}))
            self.assertEqual(rendered, "Mai")
            t = self.get_template(
                '{% load i18n %}{% translate "May" context message_context %}'
            )
            rendered = t.render(Context({"message_context": "verb"}))
            self.assertEqual(rendered, "Kann")

            # Using a filter
            t = self.get_template(
                '{% load i18n %}{% translate "May" context message_context|lower %}'
            )
            rendered = t.render(Context({"message_context": "MONTH NAME"}))
            self.assertEqual(rendered, "Mai")
            t = self.get_template(
                '{% load i18n %}{% translate "May" context message_context|lower %}'
            )
            rendered = t.render(Context({"message_context": "VERB"}))
            self.assertEqual(rendered, "Kann")

            # Using 'as'
            t = self.get_template(
                '{% load i18n %}{% translate "May" context "month name" as var %}'
                "Value: {{ var }}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "Value: Mai")
            t = self.get_template(
                '{% load i18n %}{% translate "May" as var context "verb" %}Value: '
                "{{ var }}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "Value: Kann")