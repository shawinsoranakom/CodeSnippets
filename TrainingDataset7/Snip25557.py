def test_foreign_object_to_partially_unique_field(self):
        class Person(models.Model):
            country_id = models.IntegerField()
            city_id = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["country_id", "city_id"],
                        name="tfotpuf_partial_unique",
                        condition=models.Q(pk__gt=2),
                    ),
                ]

        class MMembership(models.Model):
            person_country_id = models.IntegerField()
            person_city_id = models.IntegerField()
            person = models.ForeignObject(
                Person,
                on_delete=models.CASCADE,
                from_fields=["person_country_id", "person_city_id"],
                to_fields=["country_id", "city_id"],
            )

        field = MMembership._meta.get_field("person")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "No subset of the fields 'country_id', 'city_id' on model "
                    "'Person' is unique.",
                    hint=(
                        "Mark a single field as unique=True or add a set of "
                        "fields to a unique constraint (via unique_together or a "
                        "UniqueConstraint (without condition) in the model "
                        "Meta.constraints)."
                    ),
                    obj=field,
                    id="fields.E310",
                ),
            ],
        )