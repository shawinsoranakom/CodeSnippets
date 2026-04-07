def test_to_fields_not_checked_if_related_model_doesnt_exist(self):
        class Child(models.Model):
            a = models.PositiveIntegerField()
            b = models.PositiveIntegerField()
            parent = models.ForeignObject(
                "invalid_models_tests.Parent",
                on_delete=models.SET_NULL,
                from_fields=("a", "b"),
                to_fields=("a", "b"),
            )

        field = Child._meta.get_field("parent")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "Field defines a relation with model "
                    "'invalid_models_tests.Parent', which is either not installed, or "
                    "is abstract.",
                    id="fields.E300",
                    obj=field,
                ),
            ],
        )