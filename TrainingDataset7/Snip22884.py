def test_boundfield_fallback(self):
        class RendererWithoutBoundFieldClassAttribute:
            form_template_name = "django/forms/div.html"
            formset_template_name = "django/forms/formsets/div.html"
            field_template_name = "django/forms/field.html"

            def render(self, template_name, context, request=None):
                return "Nice"

        class UserForm(Form):
            name = CharField()

        form = UserForm(renderer=RendererWithoutBoundFieldClassAttribute())
        self.assertIsInstance(form["name"], BoundField)
        self.assertEqual(form["name"].as_field_group(), "Nice")