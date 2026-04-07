def test_check_constraint_refs_excluded_field(self):
        data = {
            "id": "",
            "name": "priceless",
            "price": "0.00",
            "category": "category 1",
        }
        ConstraintsModelForm = modelform_factory(ConstraintsModel, fields="__all__")
        ExcludePriceForm = modelform_factory(ConstraintsModel, exclude=["price"])
        full_form = ConstraintsModelForm(data)
        exclude_price_form = ExcludePriceForm(data)
        self.assertTrue(exclude_price_form.is_valid())
        self.assertFalse(full_form.is_valid())
        self.assertEqual(
            full_form.errors, {"__all__": ["Price must be greater than zero."]}
        )