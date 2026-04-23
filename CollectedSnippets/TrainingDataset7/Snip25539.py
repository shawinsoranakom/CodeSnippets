def test_ambiguous_relationship_model_to(self):
        class Person(models.Model):
            pass

        class Group(models.Model):
            field = models.ManyToManyField(
                "Person", through="AmbiguousRelationship", related_name="tertiary"
            )

        class AmbiguousRelationship(models.Model):
            # Too much foreign keys to Person.
            first_person = models.ForeignKey(
                Person, models.CASCADE, related_name="first"
            )
            second_person = models.ForeignKey(
                Person, models.CASCADE, related_name="second"
            )
            second_model = models.ForeignKey(Group, models.CASCADE)

        field = Group._meta.get_field("field")
        self.assertEqual(
            field.check(from_model=Group),
            [
                Error(
                    "The model is used as an intermediate model by "
                    "'invalid_models_tests.Group.field', but it has more than one "
                    "foreign key to 'Person', which is ambiguous. You must specify "
                    "which foreign key Django should use via the through_fields "
                    "keyword argument.",
                    hint=(
                        "If you want to create a recursive relationship, use "
                        'ManyToManyField("self", through="AmbiguousRelationship").'
                    ),
                    obj=field,
                    id="fields.E335",
                ),
            ],
        )