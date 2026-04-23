def test_nested_partials_rendering_with_context(self):
        template_source = """
        {% partialdef outer inline %}
            Hello {{ name }}!
            {% partialdef inner inline %}
                Your age is {{ age }}.
            {% endpartialdef inner %}
            Nice to meet you.
        {% endpartialdef outer %}
        """
        template = Template(template_source, origin=Origin(name="template.html"))

        context = Context({"name": "Alice", "age": 25})
        rendered = template.render(context)

        self.assertIn("Hello Alice!", rendered)
        self.assertIn("Your age is 25.", rendered)
        self.assertIn("Nice to meet you.", rendered)