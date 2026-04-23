def test_inlineformset_factory_default_renderer(self):
        class CustomRenderer(DjangoTemplates):
            pass

        class ModelFormWithDefaultRenderer(ModelForm):
            default_renderer = CustomRenderer()

        BookFormSet = inlineformset_factory(
            Author,
            Book,
            form=ModelFormWithDefaultRenderer,
            fields="__all__",
        )
        formset = BookFormSet()
        self.assertEqual(
            formset.forms[0].renderer, ModelFormWithDefaultRenderer.default_renderer
        )
        self.assertEqual(
            formset.empty_form.renderer, ModelFormWithDefaultRenderer.default_renderer
        )
        self.assertIsInstance(formset.renderer, DjangoTemplates)