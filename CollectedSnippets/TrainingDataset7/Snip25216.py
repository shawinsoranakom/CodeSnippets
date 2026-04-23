def test_fk_name_not_foreign_key_field_from_child(self):
        """
        If we specify fk_name, but it isn't a ForeignKey from the child model
        to the parent model, we should get an exception.
        """
        msg = "fk_name 'school' is not a ForeignKey to 'inline_formsets.Parent'."
        with self.assertRaisesMessage(ValueError, msg):
            inlineformset_factory(Parent, Child, fk_name="school")