def test_inheritance24(self):
        """
        Inheritance from local context without use of template loader
        """
        context_template = self.engine.from_string(
            "1{% block first %}_{% endblock %}3{% block second %}_{% endblock %}"
        )
        output = self.engine.render_to_string(
            "inheritance24", {"context_template": context_template}
        )
        self.assertEqual(output, "1234")