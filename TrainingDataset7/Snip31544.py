def test_unrelated_of_argument_raises_error(self):
        """
        FieldError is raised if a non-relation field is specified in of=(...).
        """
        msg = (
            "Invalid field name(s) given in select_for_update(of=(...)): %s. "
            "Only relational fields followed in the query are allowed. "
            "Choices are: self, born, born__country, "
            "born__country__entity_ptr."
        )
        invalid_of = [
            ("nonexistent",),
            ("name",),
            ("born__nonexistent",),
            ("born__name",),
            ("born__nonexistent", "born__name"),
        ]
        for of in invalid_of:
            with self.subTest(of=of):
                with self.assertRaisesMessage(FieldError, msg % ", ".join(of)):
                    with transaction.atomic():
                        Person.objects.select_related(
                            "born__country"
                        ).select_for_update(of=of).get()