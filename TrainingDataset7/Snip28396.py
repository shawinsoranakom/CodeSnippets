def test_save_with_data_errors(self):
        # If you call save() with invalid data, you'll get a ValueError.
        f = BaseCategoryForm({"name": "", "slug": "not a slug!", "url": "foo"})
        self.assertEqual(f.errors["name"], ["This field is required."])
        self.assertEqual(
            f.errors["slug"],
            [
                "Enter a valid “slug” consisting of letters, numbers, underscores or "
                "hyphens."
            ],
        )
        self.assertEqual(f.cleaned_data, {"url": "foo"})
        msg = "The Category could not be created because the data didn't validate."
        with self.assertRaisesMessage(ValueError, msg):
            f.save()
        f = BaseCategoryForm({"name": "", "slug": "", "url": "foo"})
        with self.assertRaisesMessage(ValueError, msg):
            f.save()