def test_serialize_managers(self):
        self.assertSerializedEqual(models.Manager())
        self.assertSerializedResultEqual(
            FoodQuerySet.as_manager(),
            (
                "migrations.models.FoodQuerySet.as_manager()",
                {"import migrations.models"},
            ),
        )
        self.assertSerializedEqual(FoodManager("a", "b"))
        self.assertSerializedEqual(FoodManager("x", "y", c=3, d=4))