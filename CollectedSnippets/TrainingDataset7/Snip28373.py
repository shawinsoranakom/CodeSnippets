def test_unique_together_exclusion(self):
        """
        Forms don't validate unique_together constraints when only part of the
        constraint is included in the form's fields. This allows using
        form.save(commit=False) and then assigning the missing field(s) to the
        model instance.
        """

        class BookForm(forms.ModelForm):
            class Meta:
                model = DerivedBook
                fields = ("isbn", "suffix1")

        # The unique_together is on suffix1/suffix2 but only suffix1 is part
        # of the form. The fields must have defaults, otherwise they'll be
        # skipped by other logic.
        self.assertEqual(DerivedBook._meta.unique_together, (("suffix1", "suffix2"),))
        for name in ("suffix1", "suffix2"):
            with self.subTest(name=name):
                field = DerivedBook._meta.get_field(name)
                self.assertEqual(field.default, 0)

        # The form fails validation with "Derived book with this Suffix1 and
        # Suffix2 already exists." if the unique_together validation isn't
        # skipped.
        DerivedBook.objects.create(isbn="12345")
        form = BookForm({"isbn": "56789", "suffix1": "0"})
        self.assertTrue(form.is_valid(), form.errors)