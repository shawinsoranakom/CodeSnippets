def test_template_name_can_be_overridden(self):
        class CustomFormSet(BaseFormSet):
            template_name = "a/custom/formset/template.html"

        ChoiceFormSet = formset_factory(Choice, formset=CustomFormSet)

        self.assertEqual(
            ChoiceFormSet().template_name, "a/custom/formset/template.html"
        )