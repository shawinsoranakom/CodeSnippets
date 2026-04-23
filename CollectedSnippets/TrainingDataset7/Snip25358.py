def test_ordering_pointing_to_non_related_field(self):
        class Child(models.Model):
            parent = models.IntegerField()

            class Meta:
                ordering = ("parent__missing_field",)

        self.assertEqual(
            Child.check(),
            [
                Error(
                    "'ordering' refers to the nonexistent field, related field, "
                    "or lookup 'parent__missing_field'.",
                    obj=Child,
                    id="models.E015",
                )
            ],
        )