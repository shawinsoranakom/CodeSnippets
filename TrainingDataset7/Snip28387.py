def test_override_unique_together_message(self):
        class CustomPriceForm(PriceForm):
            class Meta(PriceForm.Meta):
                error_messages = {
                    NON_FIELD_ERRORS: {
                        "unique_together": (
                            "%(model_name)s's %(field_labels)s not unique."
                        ),
                    }
                }

        Price.objects.create(price=6.00, quantity=1)
        form = CustomPriceForm({"price": "6.00", "quantity": "1"})
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors[NON_FIELD_ERRORS], ["Price's Price and Quantity not unique."]
        )