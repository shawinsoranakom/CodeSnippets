def test_many_to_many_field(self):
        with self.assertRaisesMessage(
            FieldError, self.invalid_error % ("toppings", "(none)")
        ):
            list(Pizza.objects.select_related("toppings"))