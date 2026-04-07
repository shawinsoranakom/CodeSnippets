def test_hash(self):
        self.assertEqual(hash(Q()), hash(Q()))
        self.assertEqual(
            hash(Q(("pk__in", (1, 2)))),
            hash(Q(("pk__in", [1, 2]))),
        )
        self.assertEqual(
            hash(Q(("pk__in", (1, 2)))),
            hash(Q(pk__in=[1, 2])),
        )
        self.assertEqual(
            hash(Q(("pk__in", (1, 2)))),
            hash(Q(("pk__in", {1: "first", 2: "second"}.keys()))),
        )
        self.assertNotEqual(
            hash(Q(name__iexact=F("other_name"))),
            hash(Q(name=Lower(F("other_name")))),
        )