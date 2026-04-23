def test_save_commit_false(self):
        # If you call save() with commit=False, then it will return an object
        # that hasn't yet been saved to the database. In this case, it's up to
        # you to call save() on the resulting model instance.
        f = BaseCategoryForm(
            {"name": "Third test", "slug": "third-test", "url": "third"}
        )
        self.assertTrue(f.is_valid())
        c1 = f.save(commit=False)
        self.assertEqual(c1.name, "Third test")
        self.assertEqual(Category.objects.count(), 0)
        c1.save()
        self.assertEqual(Category.objects.count(), 1)