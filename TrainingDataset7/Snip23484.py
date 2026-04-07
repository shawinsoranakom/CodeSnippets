def test_meta_widgets(self):
        """TaggedItemForm has a widget defined in Meta."""
        Formset = generic_inlineformset_factory(TaggedItem, TaggedItemForm)
        form = Formset().forms[0]
        self.assertIsInstance(form["tag"].field.widget, CustomWidget)