def test_extends_generic_template(self):
        """
        #24338 -- Allow extending django.template.backends.django.Template
        objects.
        """
        engine = self._engine()
        parent = engine.from_string("{% block content %}parent{% endblock %}")
        child = engine.from_string(
            "{% extends parent %}{% block content %}child{% endblock %}"
        )
        self.assertEqual(child.render(Context({"parent": parent})), "child")