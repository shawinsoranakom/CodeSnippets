def test_unique_null(self):
        title = "I May Be Wrong But I Doubt It"
        form = BookForm({"title": title, "author": self.writer.pk})
        self.assertTrue(form.is_valid())
        form.save()
        form = BookForm({"title": title, "author": self.writer.pk})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["__all__"], ["Book with this Title and Author already exists."]
        )
        form = BookForm({"title": title})
        self.assertTrue(form.is_valid())
        form.save()
        form = BookForm({"title": title})
        self.assertTrue(form.is_valid())