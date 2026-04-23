def test_unique_m2m(self):
        class Person(models.Model):
            name = models.CharField(max_length=5)

        class Group(models.Model):
            members = models.ManyToManyField("Person", unique=True)

        field = Group._meta.get_field("members")
        self.assertEqual(
            field.check(from_model=Group),
            [
                Error(
                    "ManyToManyFields cannot be unique.",
                    obj=field,
                    id="fields.E330",
                ),
            ],
        )