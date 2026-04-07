def test_partials_with_duplicate_names(self):
        test_cases = [
            (
                "nested",
                """
                {% partialdef duplicate %}{% partialdef duplicate %}
                CONTENT
                {% endpartialdef %}{% endpartialdef %}
                """,
            ),
            (
                "conditional",
                """
                {% if ... %}
                  {% partialdef duplicate %}
                  CONTENT
                  {% endpartialdef %}
                {% else %}
                  {% partialdef duplicate %}
                  OTHER-CONTENT
                  {% endpartialdef %}
                {% endif %}
                """,
            ),
        ]

        for test_name, template_source in test_cases:
            with self.subTest(test_name=test_name):
                with self.assertRaisesMessage(
                    TemplateSyntaxError,
                    "Partial 'duplicate' is already defined in the "
                    "'template.html' template.",
                ):
                    Template(template_source, origin=Origin(name="template.html"))