def test_field_name_clash_with_m2m_through(self):
        class Parent(models.Model):
            clash_id = models.IntegerField()

        class Child(Parent):
            clash = models.ForeignKey("Child", models.CASCADE)

        class Model(models.Model):
            parents = models.ManyToManyField(
                to=Parent,
                through="Through",
                through_fields=["parent", "model"],
            )

        class Through(models.Model):
            parent = models.ForeignKey(Parent, models.CASCADE)
            model = models.ForeignKey(Model, models.CASCADE)

        self.assertEqual(
            Child.check(),
            [
                Error(
                    "The field 'clash' clashes with the field 'clash_id' from "
                    "model 'invalid_models_tests.parent'.",
                    obj=Child._meta.get_field("clash"),
                    id="models.E006",
                )
            ],
        )