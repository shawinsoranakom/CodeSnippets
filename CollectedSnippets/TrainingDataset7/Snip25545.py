def test_too_many_foreign_keys_in_self_referential_model(self):
        class Person(models.Model):
            friends = models.ManyToManyField(
                "self", through="InvalidRelationship", symmetrical=False
            )

        class InvalidRelationship(models.Model):
            first = models.ForeignKey(
                Person, models.CASCADE, related_name="rel_from_set_2"
            )
            second = models.ForeignKey(
                Person, models.CASCADE, related_name="rel_to_set_2"
            )
            third = models.ForeignKey(
                Person, models.CASCADE, related_name="too_many_by_far"
            )

        field = Person._meta.get_field("friends")
        self.assertEqual(
            field.check(from_model=Person),
            [
                Error(
                    "The model is used as an intermediate model by "
                    "'invalid_models_tests.Person.friends', but it has more than two "
                    "foreign keys to 'Person', which is ambiguous. You must specify "
                    "which two foreign keys Django should use via the through_fields "
                    "keyword argument.",
                    hint=(
                        "Use through_fields to specify which two foreign keys Django "
                        "should use."
                    ),
                    obj=InvalidRelationship,
                    id="fields.E333",
                ),
            ],
        )