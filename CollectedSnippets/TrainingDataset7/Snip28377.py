def test_inherited_unique_together(self):
        title = "Boss"
        form = BookForm({"title": title, "author": self.writer.pk})
        self.assertTrue(form.is_valid())
        form.save()
        form = DerivedBookForm(
            {"title": title, "author": self.writer.pk, "isbn": "12345"}
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["__all__"], ["Book with this Title and Author already exists."]
        )