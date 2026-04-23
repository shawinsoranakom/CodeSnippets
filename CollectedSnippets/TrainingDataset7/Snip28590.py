def test_inlineformset_factory_passes_renderer(self):
        from django.forms.renderers import Jinja2

        renderer = Jinja2()
        BookFormSet = inlineformset_factory(
            Author,
            Book,
            fields="__all__",
            renderer=renderer,
        )
        formset = BookFormSet()
        self.assertEqual(formset.renderer, renderer)