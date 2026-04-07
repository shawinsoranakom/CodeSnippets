def test_modelformset_factory_passes_renderer(self):
        from django.forms.renderers import Jinja2

        renderer = Jinja2()
        BookFormSet = modelformset_factory(Author, fields="__all__", renderer=renderer)
        formset = BookFormSet()
        self.assertEqual(formset.renderer, renderer)