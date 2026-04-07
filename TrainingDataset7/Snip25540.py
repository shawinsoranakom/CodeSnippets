def test_relationship_model_with_foreign_key_to_wrong_model(self):
        class WrongModel(models.Model):
            pass

        class Person(models.Model):
            pass

        class Group(models.Model):
            members = models.ManyToManyField("Person", through="InvalidRelationship")

        class InvalidRelationship(models.Model):
            person = models.ForeignKey(Person, models.CASCADE)
            wrong_foreign_key = models.ForeignKey(WrongModel, models.CASCADE)
            # The last foreign key should point to Group model.

        field = Group._meta.get_field("members")
        self.assertEqual(
            field.check(from_model=Group),
            [
                Error(
                    "The model is used as an intermediate model by "
                    "'invalid_models_tests.Group.members', but it does not "
                    "have a foreign key to 'Group' or 'Person'.",
                    obj=InvalidRelationship,
                    id="fields.E336",
                ),
            ],
        )