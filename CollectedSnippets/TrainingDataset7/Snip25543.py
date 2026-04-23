def test_missing_relationship_model_on_model_check(self):
        class Person(models.Model):
            pass

        class Group(models.Model):
            members = models.ManyToManyField("Person", through="MissingM2MModel")

        self.assertEqual(
            Group.check(),
            [
                Error(
                    "Field specifies a many-to-many relation through model "
                    "'MissingM2MModel', which has not been installed.",
                    obj=Group._meta.get_field("members"),
                    id="fields.E331",
                ),
            ],
        )