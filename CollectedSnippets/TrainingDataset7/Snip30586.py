def test_reasonable_number_of_subq_aliases(self):
        x = Tag.objects.filter(pk=1)
        for _ in range(20):
            x = Tag.objects.filter(pk__in=x)
        self.assertEqual(
            x.query.subq_aliases,
            {
                "T",
                "U",
                "V",
                "W",
                "X",
                "Y",
                "Z",
                "AA",
                "AB",
                "AC",
                "AD",
                "AE",
                "AF",
                "AG",
                "AH",
                "AI",
                "AJ",
                "AK",
                "AL",
                "AM",
                "AN",
            },
        )