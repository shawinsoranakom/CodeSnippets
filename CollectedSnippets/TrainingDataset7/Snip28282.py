def test_clean_model_instance(self):
        f = forms.ModelChoiceField(Category.objects.all())
        self.assertEqual(f.clean(self.c1), self.c1)
        # An instance of incorrect model.
        msg = (
            "['Select a valid choice. That choice is not one of the available "
            "choices.']"
        )
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(Book.objects.create())