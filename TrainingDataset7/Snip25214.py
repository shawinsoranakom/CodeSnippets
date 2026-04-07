def test_inline_formset_factory(self):
        """
        These should both work without a problem.
        """
        inlineformset_factory(Parent, Child, fk_name="mother", fields="__all__")
        inlineformset_factory(Parent, Child, fk_name="father", fields="__all__")