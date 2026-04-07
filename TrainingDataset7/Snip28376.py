def test_inherited_unique(self):
        title = "Boss"
        Book.objects.create(title=title, author=self.writer, special_id=1)
        form = DerivedBookForm(
            {
                "title": "Other",
                "author": self.writer.pk,
                "special_id": "1",
                "isbn": "12345",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["special_id"], ["Book with this Special id already exists."]
        )