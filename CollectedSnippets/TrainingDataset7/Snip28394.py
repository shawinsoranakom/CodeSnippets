def test_basic_creation(self):
        self.assertEqual(Category.objects.count(), 0)
        f = BaseCategoryForm(
            {
                "name": "Entertainment",
                "slug": "entertainment",
                "url": "entertainment",
            }
        )
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["name"], "Entertainment")
        self.assertEqual(f.cleaned_data["slug"], "entertainment")
        self.assertEqual(f.cleaned_data["url"], "entertainment")
        c1 = f.save()
        # Testing whether the same object is returned from the
        # ORM... not the fastest way...

        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(c1, Category.objects.all()[0])
        self.assertEqual(c1.name, "Entertainment")