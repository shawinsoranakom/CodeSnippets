def test_bound_field_sanity_check(self):
        field = models.CharField(max_length=1)
        field.model = models.Model
        with self.assertRaisesMessage(
            ValueError, 'ModelState.fields cannot be bound to a model - "field" is.'
        ):
            ModelState("app", "Model", [("field", field)])