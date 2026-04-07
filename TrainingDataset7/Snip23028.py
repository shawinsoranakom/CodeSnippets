def test_custom_renderer(self):
        """
        A custom renderer passed to a formset_factory() is passed to all forms
        and ErrorList.
        """
        from django.forms.renderers import Jinja2

        renderer = Jinja2()
        data = {
            "choices-TOTAL_FORMS": "2",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-0-choice": "Zero",
            "choices-0-votes": "",
            "choices-1-choice": "One",
            "choices-1-votes": "",
        }
        ChoiceFormSet = formset_factory(Choice, renderer=renderer)
        formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertEqual(formset.renderer, renderer)
        self.assertEqual(formset.forms[0].renderer, renderer)
        self.assertEqual(formset.management_form.renderer, renderer)
        self.assertEqual(formset.non_form_errors().renderer, renderer)
        self.assertEqual(formset.empty_form.renderer, renderer)