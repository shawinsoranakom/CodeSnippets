def test_intersection_foreign_object(self):
        class Parent(models.Model):
            a = models.PositiveIntegerField()
            b = models.PositiveIntegerField()
            c = models.PositiveIntegerField()
            d = models.PositiveIntegerField()

            class Meta:
                unique_together = (("a", "b", "c"),)

        class Child(models.Model):
            a = models.PositiveIntegerField()
            b = models.PositiveIntegerField()
            d = models.PositiveIntegerField()
            value = models.CharField(max_length=255)
            parent = models.ForeignObject(
                Parent,
                on_delete=models.SET_NULL,
                from_fields=("a", "b", "d"),
                to_fields=("a", "b", "d"),
                related_name="children",
            )

        field = Child._meta.get_field("parent")
        self.assertEqual(
            field.check(from_model=Child),
            [
                Error(
                    "No subset of the fields 'a', 'b', 'd' on model 'Parent' is "
                    "unique.",
                    hint=(
                        "Mark a single field as unique=True or add a set of "
                        "fields to a unique constraint (via unique_together or a "
                        "UniqueConstraint (without condition) in the model "
                        "Meta.constraints)."
                    ),
                    obj=field,
                    id="fields.E310",
                ),
            ],
        )