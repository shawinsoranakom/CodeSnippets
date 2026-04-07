def test_ordering_pointing_to_two_related_model_field(self):
        class Parent2(models.Model):
            pass

        class Parent1(models.Model):
            parent2 = models.ForeignKey(Parent2, models.CASCADE)

        class Child(models.Model):
            parent1 = models.ForeignKey(Parent1, models.CASCADE)

            class Meta:
                ordering = ("parent1__parent2__missing_field",)

        self.assertEqual(
            Child.check(),
            [
                Error(
                    "'ordering' refers to the nonexistent field, related field, "
                    "or lookup 'parent1__parent2__missing_field'.",
                    obj=Child,
                    id="models.E015",
                )
            ],
        )