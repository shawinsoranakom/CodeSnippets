def test_inline_formsets_with_wrong_fk_name(self):
        """Regression for #23451"""
        message = "fk_name 'title' is not a ForeignKey to 'model_formsets.Author'."
        with self.assertRaisesMessage(ValueError, message):
            inlineformset_factory(Author, Book, fields="__all__", fk_name="title")