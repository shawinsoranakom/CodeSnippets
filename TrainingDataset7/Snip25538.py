def test_ambiguous_relationship_model_from(self):
        class Person(models.Model):
            pass

        class Group(models.Model):
            field = models.ManyToManyField("Person", through="AmbiguousRelationship")

        class AmbiguousRelationship(models.Model):
            person = models.ForeignKey(Person, models.CASCADE)
            first_group = models.ForeignKey(Group, models.CASCADE, related_name="first")
            second_group = models.ForeignKey(
                Group, models.CASCADE, related_name="second"
            )

        field = Group._meta.get_field("field")
        self.assertEqual(
            field.check(from_model=Group),
            [
                Error(
                    "The model is used as an intermediate model by "
                    "'invalid_models_tests.Group.field', but it has more than one "
                    "foreign key from 'Group', which is ambiguous. You must "
                    "specify which foreign key Django should use via the "
                    "through_fields keyword argument.",
                    hint=(
                        "If you want to create a recursive relationship, use "
                        'ManyToManyField("self", through="AmbiguousRelationship").'
                    ),
                    obj=field,
                    id="fields.E334",
                ),
            ],
        )