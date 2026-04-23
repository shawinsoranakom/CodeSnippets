def test_unique_together(self):
        """ModelForm test of unique_together constraint"""
        form = PriceForm({"price": "6.00", "quantity": "1"})
        self.assertTrue(form.is_valid())
        form.save()
        form = PriceForm({"price": "6.00", "quantity": "1"})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["__all__"],
            ["Price with this Price and Quantity already exists."],
        )