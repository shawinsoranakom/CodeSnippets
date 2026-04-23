def test_template_tags_pgettext(self):
        """
        {% blocktranslate %} takes message contexts into account (#14806).
        """
        trans_real._active = Local()
        trans_real._translations = {}
        with translation.override("de"):
            # Nonexistent context
            t = self.get_template(
                '{% load i18n %}{% blocktranslate context "nonexistent" %}May'
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "May")

            # Existing context... using a literal
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate context "month name" %}May{% endblocktranslate %}'
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "Mai")
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate context "verb" %}May{% endblocktranslate %}'
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "Kann")

            # Using a variable
            t = self.get_template(
                "{% load i18n %}{% blocktranslate context message_context %}"
                "May{% endblocktranslate %}"
            )
            rendered = t.render(Context({"message_context": "month name"}))
            self.assertEqual(rendered, "Mai")
            t = self.get_template(
                "{% load i18n %}{% blocktranslate context message_context %}"
                "May{% endblocktranslate %}"
            )
            rendered = t.render(Context({"message_context": "verb"}))
            self.assertEqual(rendered, "Kann")

            # Using a filter
            t = self.get_template(
                "{% load i18n %}"
                "{% blocktranslate context message_context|lower %}May"
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context({"message_context": "MONTH NAME"}))
            self.assertEqual(rendered, "Mai")
            t = self.get_template(
                "{% load i18n %}"
                "{% blocktranslate context message_context|lower %}May"
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context({"message_context": "VERB"}))
            self.assertEqual(rendered, "Kann")

            # Using 'count'
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate count number=1 context "super search" %}{{ number }}'
                " super result{% plural %}{{ number }} super results"
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "1 Super-Ergebnis")
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate count number=2 context "super search" %}{{ number }}'
                " super result{% plural %}{{ number }} super results"
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "2 Super-Ergebnisse")
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate context "other super search" count number=1 %}'
                "{{ number }} super result{% plural %}{{ number }} super results"
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "1 anderen Super-Ergebnis")
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate context "other super search" count number=2 %}'
                "{{ number }} super result{% plural %}{{ number }} super results"
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "2 andere Super-Ergebnisse")

            # Using 'with'
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate with num_comments=5 context "comment count" %}'
                "There are {{ num_comments }} comments{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "Es gibt 5 Kommentare")
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate with num_comments=5 context "other comment count" %}'
                "There are {{ num_comments }} comments{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "Andere: Es gibt 5 Kommentare")

            # Using trimmed
            t = self.get_template(
                "{% load i18n %}{% blocktranslate trimmed %}\n\nThere\n\t are 5  "
                "\n\n   comments\n{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "There are 5 comments")
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate with num_comments=5 context "comment count" trimmed '
                "%}\n\n"
                "There are  \t\n  \t {{ num_comments }} comments\n\n"
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "Es gibt 5 Kommentare")
            t = self.get_template(
                "{% load i18n %}"
                '{% blocktranslate context "other super search" count number=2 trimmed '
                "%}\n{{ number }} super \n result{% plural %}{{ number }} super results"
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context())
            self.assertEqual(rendered, "2 andere Super-Ergebnisse")

            # Misuses
            msg = "Unknown argument for 'blocktranslate' tag: %r."
            with self.assertRaisesMessage(TemplateSyntaxError, msg % 'month="May"'):
                self.get_template(
                    '{% load i18n %}{% blocktranslate context with month="May" %}'
                    "{{ month }}{% endblocktranslate %}"
                )
            msg = (
                '"context" in %r tag expected exactly one argument.' % "blocktranslate"
            )
            with self.assertRaisesMessage(TemplateSyntaxError, msg):
                self.get_template(
                    "{% load i18n %}{% blocktranslate context %}{% endblocktranslate %}"
                )
            with self.assertRaisesMessage(TemplateSyntaxError, msg):
                self.get_template(
                    "{% load i18n %}{% blocktranslate count number=2 context %}"
                    "{{ number }} super result{% plural %}{{ number }}"
                    " super results{% endblocktranslate %}"
                )