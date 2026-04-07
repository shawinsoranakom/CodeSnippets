def test_unique_validation(self):
        FormSet = modelformset_factory(Product, fields="__all__", extra=1)
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-slug": "car-red",
        }
        formset = FormSet(data)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (product1,) = saved
        self.assertEqual(product1.slug, "car-red")

        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-slug": "car-red",
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset.errors, [{"slug": ["Product with this Slug already exists."]}]
        )