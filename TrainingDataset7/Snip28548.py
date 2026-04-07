def test_unique_together_validation(self):
        FormSet = modelformset_factory(Price, fields="__all__", extra=1)
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-price": "12.00",
            "form-0-quantity": "1",
        }
        formset = FormSet(data)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (price1,) = saved
        self.assertEqual(price1.price, Decimal("12.00"))
        self.assertEqual(price1.quantity, 1)

        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-price": "12.00",
            "form-0-quantity": "1",
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset.errors,
            [{"__all__": ["Price with this Price and Quantity already exists."]}],
        )