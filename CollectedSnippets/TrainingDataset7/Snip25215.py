def test_exception_on_unspecified_foreign_key(self):
        """
        Child has two ForeignKeys to Parent, so if we don't specify which one
        to use for the inline formset, we should get an exception.
        """
        msg = (
            "'inline_formsets.Child' has more than one ForeignKey to "
            "'inline_formsets.Parent'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            inlineformset_factory(Parent, Child)