def test_form_default_renderer_class(self):
        """
        In the absence of a renderer passed to the formset_factory(),
        Form.default_renderer is respected.
        """

        class CustomRenderer(DjangoTemplates):
            pass

        class ChoiceWithDefaultRenderer(Choice):
            default_renderer = CustomRenderer

        data = {
            "choices-TOTAL_FORMS": "1",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
        }

        ChoiceFormSet = formset_factory(ChoiceWithDefaultRenderer)
        formset = ChoiceFormSet(data, prefix="choices")
        self.assertIsInstance(formset.forms[0].renderer, CustomRenderer)
        self.assertIsInstance(formset.empty_form.renderer, CustomRenderer)
        default_renderer = get_default_renderer()
        self.assertIsInstance(formset.renderer, type(default_renderer))