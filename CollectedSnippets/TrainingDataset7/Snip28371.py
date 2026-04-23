def test_simple_unique(self):
        form = ProductForm({"slug": "teddy-bear-blue"})
        self.assertTrue(form.is_valid())
        obj = form.save()
        form = ProductForm({"slug": "teddy-bear-blue"})
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["slug"], ["Product with this Slug already exists."]
        )
        form = ProductForm({"slug": "teddy-bear-blue"}, instance=obj)
        self.assertTrue(form.is_valid())