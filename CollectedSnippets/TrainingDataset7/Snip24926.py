def test_kwargs(self):
        tpl = Template("""
            {% load i18n %}
            {% language 'nl'  %}
            {% url 'no-prefix-translated-slug' slug='apo' %}{% endlanguage %}
            {% language 'pt-br' %}
            {% url 'no-prefix-translated-slug' slug='apo' %}{% endlanguage %}
            """)
        self.assertEqual(
            tpl.render(Context({})).strip().split(),
            ["/vertaald/apo/", "/traduzidos/apo/"],
        )