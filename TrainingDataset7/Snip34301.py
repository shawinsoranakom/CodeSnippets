def test_extends_not_first_tag_in_extended_template_from_string(self):
        template_string = "{% block content %}B{% endblock %}{% extends 'base.html' %}"
        msg = "{% extends 'base.html' %} must be the first tag in the template."
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Engine().from_string(template_string)