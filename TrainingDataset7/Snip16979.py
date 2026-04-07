def test_values_annotation_with_expression(self):
        # ensure the F() is promoted to the group by clause
        qs = Author.objects.values("name").annotate(another_age=Sum("age") + F("age"))
        a = qs.get(name="Adrian Holovaty")
        self.assertEqual(a["another_age"], 68)

        qs = qs.annotate(friend_count=Count("friends"))
        a = qs.get(name="Adrian Holovaty")
        self.assertEqual(a["friend_count"], 2)

        qs = (
            qs.annotate(combined_age=Sum("age") + F("friends__age"))
            .filter(name="Adrian Holovaty")
            .order_by("-combined_age")
        )
        self.assertEqual(
            list(qs),
            [
                {
                    "name": "Adrian Holovaty",
                    "another_age": 68,
                    "friend_count": 1,
                    "combined_age": 69,
                },
                {
                    "name": "Adrian Holovaty",
                    "another_age": 68,
                    "friend_count": 1,
                    "combined_age": 63,
                },
            ],
        )

        vals = qs.values("name", "combined_age")
        self.assertEqual(
            list(vals),
            [
                {"name": "Adrian Holovaty", "combined_age": 69},
                {"name": "Adrian Holovaty", "combined_age": 63},
            ],
        )