def test_equal(self):
        self.assertEqual(Q(), Q())
        self.assertEqual(
            Q(("pk__in", (1, 2))),
            Q(("pk__in", [1, 2])),
        )
        self.assertEqual(
            Q(("pk__in", (1, 2))),
            Q(pk__in=[1, 2]),
        )
        self.assertEqual(
            Q(("pk__in", (1, 2))),
            Q(("pk__in", {1: "first", 2: "second"}.keys())),
        )
        self.assertNotEqual(
            Q(name__iexact=F("other_name")),
            Q(name=Lower(F("other_name"))),
        )