def test_relationship_model_missing_foreign_key(self):
        class Person(models.Model):
            pass

        class Group(models.Model):
            members = models.ManyToManyField("Person", through="InvalidRelationship")

        class InvalidRelationship(models.Model):
            group = models.ForeignKey(Group, models.CASCADE)
            # No foreign key to Person

        field = Group._meta.get_field("members")
        self.assertEqual(
            field.check(from_model=Group),
            [
                Error(
                    "The model is used as an intermediate model by "
                    "'invalid_models_tests.Group.members', but it does not have "
                    "a foreign key to 'Group' or 'Person'.",
                    obj=InvalidRelationship,
                    id="fields.E336",
                ),
            ],
        )