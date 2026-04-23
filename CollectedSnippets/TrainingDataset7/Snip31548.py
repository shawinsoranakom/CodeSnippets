def test_reverse_one_to_one_of_arguments(self):
        """
        Reverse OneToOneFields may be included in of=(...) as long as NULLs
        are excluded because LEFT JOIN isn't allowed in SELECT FOR UPDATE.
        """
        with transaction.atomic():
            person = (
                Person.objects.select_related(
                    "profile",
                )
                .exclude(profile=None)
                .select_for_update(of=("profile",))
                .get()
            )
            self.assertEqual(person.profile, self.person_profile)