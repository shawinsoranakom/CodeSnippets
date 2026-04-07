def test_non_foreign_key_field(self):
        """
        If the field specified in fk_name is not a ForeignKey, we should get an
        exception.
        """
        with self.assertRaisesMessage(
            ValueError, "'inline_formsets.Child' has no field named 'test'."
        ):
            inlineformset_factory(Parent, Child, fk_name="test")