def test_two_m2m_through_same_relationship(self):
        class Person(models.Model):
            pass

        class Group(models.Model):
            primary = models.ManyToManyField(
                Person, through="Membership", related_name="primary"
            )
            secondary = models.ManyToManyField(
                Person, through="Membership", related_name="secondary"
            )

        class Membership(models.Model):
            person = models.ForeignKey(Person, models.CASCADE)
            group = models.ForeignKey(Group, models.CASCADE)

        self.assertEqual(
            Group.check(),
            [
                Error(
                    "The model has two identical many-to-many relations through "
                    "the intermediate model 'invalid_models_tests.Membership'.",
                    obj=Group,
                    id="models.E003",
                )
            ],
        )