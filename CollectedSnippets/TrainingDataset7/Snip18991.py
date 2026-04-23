def test_non_auto_increment_pk(self):
        State.objects.bulk_create(
            [State(two_letter_code=s) for s in ["IL", "NY", "CA", "ME"]]
        )
        self.assertQuerySetEqual(
            State.objects.order_by("two_letter_code"),
            [
                "CA",
                "IL",
                "ME",
                "NY",
            ],
            attrgetter("two_letter_code"),
        )