def test_unique_constraint_refs_excluded_field(self):
        obj = ConstraintsModel.objects.create(name="product", price="1.00")
        data = {
            "id": "",
            "name": obj.name,
            "price": "1337.00",
            "category": obj.category,
        }
        ConstraintsModelForm = modelform_factory(ConstraintsModel, fields="__all__")
        ExcludeCategoryForm = modelform_factory(ConstraintsModel, exclude=["category"])
        full_form = ConstraintsModelForm(data)
        exclude_category_form = ExcludeCategoryForm(data)
        self.assertTrue(exclude_category_form.is_valid())
        self.assertFalse(full_form.is_valid())
        self.assertEqual(
            full_form.errors, {"__all__": ["This product already exists."]}
        )