def test_ordering_pointing_multiple_times_to_model_fields(self):
        class Parent(models.Model):
            field1 = models.CharField(max_length=100)
            field2 = models.CharField(max_length=100)

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.CASCADE)

            class Meta:
                ordering = ("parent__field1__field2",)

        self.assertEqual(
            Child.check(),
            [
                Error(
                    "'ordering' refers to the nonexistent field, related field, "
                    "or lookup 'parent__field1__field2'.",
                    obj=Child,
                    id="models.E015",
                )
            ],
        )