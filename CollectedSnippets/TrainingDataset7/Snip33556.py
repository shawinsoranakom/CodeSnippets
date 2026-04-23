def test_inheritance25(self):
        """
        Inheritance from local context with variable parent template
        """
        context_template = [
            self.engine.from_string("Wrong"),
            self.engine.from_string(
                "1{% block first %}_{% endblock %}3{% block second %}_{% endblock %}"
            ),
        ]
        output = self.engine.render_to_string(
            "inheritance25", {"context_template": context_template}
        )
        self.assertEqual(output, "1234")