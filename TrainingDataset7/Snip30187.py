def test_ambiguous(self):
        # Ambiguous: Lookup was already seen with a different queryset.
        msg = (
            "'houses' lookup was already seen with a different queryset. You "
            "may need to adjust the ordering of your lookups."
        )
        # lookup.queryset shouldn't be evaluated.
        with self.assertNumQueries(3):
            with self.assertRaisesMessage(ValueError, msg):
                self.traverse_qs(
                    Person.objects.prefetch_related(
                        "houses__rooms",
                        Prefetch("houses", queryset=House.objects.all()),
                    ),
                    [["houses", "rooms"]],
                )

        # Ambiguous: Lookup houses_lst doesn't yet exist when performing
        # houses_lst__rooms.
        msg = (
            "Cannot find 'houses_lst' on Person object, 'houses_lst__rooms' is "
            "an invalid parameter to prefetch_related()"
        )
        with self.assertRaisesMessage(AttributeError, msg):
            self.traverse_qs(
                Person.objects.prefetch_related(
                    "houses_lst__rooms",
                    Prefetch(
                        "houses", queryset=House.objects.all(), to_attr="houses_lst"
                    ),
                ),
                [["houses", "rooms"]],
            )

        # Not ambiguous.
        self.traverse_qs(
            Person.objects.prefetch_related("houses__rooms", "houses"),
            [["houses", "rooms"]],
        )

        self.traverse_qs(
            Person.objects.prefetch_related(
                "houses__rooms",
                Prefetch("houses", queryset=House.objects.all(), to_attr="houses_lst"),
            ),
            [["houses", "rooms"]],
        )