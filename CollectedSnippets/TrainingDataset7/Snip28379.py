def test_abstract_inherited_unique_together(self):
        title = "Boss"
        isbn = "12345"
        DerivedBook.objects.create(title=title, author=self.writer, isbn=isbn)
        form = DerivedBookForm(
            {
                "title": "Other",
                "author": self.writer.pk,
                "isbn": "9876",
                "suffix1": "0",
                "suffix2": "0",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["__all__"],
            ["Derived book with this Suffix1 and Suffix2 already exists."],
        )