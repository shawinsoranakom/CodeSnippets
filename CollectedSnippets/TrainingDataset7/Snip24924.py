def test_context(self):
        ctx = Context({"lang1": "nl", "lang2": "pt-br"})
        tpl = Template("""{% load i18n %}
            {% language lang1 %}{% url 'no-prefix-translated' %}{% endlanguage %}
            {% language lang2 %}{% url 'no-prefix-translated' %}{% endlanguage %}""")
        self.assertEqual(
            tpl.render(ctx).strip().split(), ["/vertaald/", "/traduzidos/"]
        )