def test_strings_only(self):
        t = Template("""{% load i18n %}
            {% language 'nl' %}{% url 'no-prefix-translated' %}{% endlanguage %}
            {% language 'pt-br' %}{% url 'no-prefix-translated' %}{% endlanguage %}""")
        self.assertEqual(
            t.render(Context({})).strip().split(), ["/vertaald/", "/traduzidos/"]
        )