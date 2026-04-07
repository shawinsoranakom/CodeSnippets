def test_formset_with_none_instance(self):
        "A formset with instance=None can be created. Regression for #11872"
        Form = modelform_factory(User, fields="__all__")
        FormSet = inlineformset_factory(User, UserSite, fields="__all__")

        # Instantiate the Form and FormSet to prove
        # you can create a formset with an instance of None
        Form(instance=None)
        FormSet(instance=None)