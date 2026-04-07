def test_abstract_inherited_unique(self):
        title = "Boss"
        isbn = "12345"
        DerivedBook.objects.create(title=title, author=self.writer, isbn=isbn)
        form = DerivedBookForm(
            {
                "title": "Other",
                "author": self.writer.pk,
                "isbn": isbn,
                "suffix1": "1",
                "suffix2": "2",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["isbn"], ["Derived book with this Isbn already exists."]
        )