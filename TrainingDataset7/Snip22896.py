def test_cyclic_context_boundfield_render(self):
        class FirstNameForm(Form):
            first_name = CharField()
            template_name_label = "forms_tests/cyclic_context_boundfield_render.html"

        f = FirstNameForm()
        try:
            f.render()
        except RecursionError:
            self.fail("Cyclic reference in BoundField.render().")