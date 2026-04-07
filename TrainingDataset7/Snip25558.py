def test_foreign_object_to_unique_field_with_meta_constraint(self):
        class Person(models.Model):
            country_id = models.IntegerField()
            city_id = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["country_id", "city_id"],
                        name="tfotpuf_unique",
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
        self.assertEqual(field.check(), [])