def test_clash_between_rel_name_and_manager_non_self_referential(self):
        class Thing(models.Model):
            items = models.Manager()

        class Item(models.Model):
            thing = models.ForeignKey(Thing, models.CASCADE, related_name="items")
            something = models.ForeignKey(Thing, models.CASCADE, related_name="+")

        self.assertEqual(
            Item.check(),
            [
                Error(
                    "Related name 'items' for 'invalid_models_tests.Item.thing' "
                    "clashes with the name of a model manager.",
                    hint=(
                        "Rename the model manager or change the related_name argument "
                        "in the definition for field 'invalid_models_tests.Item.thing'."
                    ),
                    obj=Item._meta.get_field("thing"),
                    id="fields.E348",
                )
            ],
        )
        self.assertEqual(Thing.check(), [])