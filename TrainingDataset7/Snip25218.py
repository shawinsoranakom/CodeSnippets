def test_any_iterable_allowed_as_argument_to_exclude(self):
        # Regression test for #9171.
        inlineformset_factory(Parent, Child, exclude=["school"], fk_name="mother")

        inlineformset_factory(Parent, Child, exclude=("school",), fk_name="mother")