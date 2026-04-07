def test_related_but_unselected_of_argument_raises_error(self):
        """
        FieldError is raised if a relation field that is not followed in the
        query is specified in of=(...).
        """
        msg = (
            "Invalid field name(s) given in select_for_update(of=(...)): %s. "
            "Only relational fields followed in the query are allowed. "
            "Choices are: self, born, profile."
        )
        for name in ["born__country", "died", "died__country"]:
            with self.subTest(name=name):
                with self.assertRaisesMessage(FieldError, msg % name):
                    with transaction.atomic():
                        Person.objects.select_related("born", "profile").exclude(
                            profile=None
                        ).select_for_update(of=(name,)).get()