def test_missing_relationship_model(self):
        class Person(models.Model):
            pass

        class Group(models.Model):
            members = models.ManyToManyField("Person", through="MissingM2MModel")

        field = Group._meta.get_field("members")
        self.assertEqual(
            field.check(from_model=Group),
            [
                Error(
                    "Field specifies a many-to-many relation through model "
                    "'MissingM2MModel', which has not been installed.",
                    obj=field,
                    id="fields.E331",
                ),
            ],
        )