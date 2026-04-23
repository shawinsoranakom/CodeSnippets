def test_defer_values_does_not_defer(self):
        # User values() won't defer anything (you get the full list of
        # dictionaries back), but it still works.
        self.assertEqual(
            Primary.objects.defer("name").values()[0],
            {
                "id": self.p1.id,
                "name": "p1",
                "value": "xx",
                "related_id": self.s1.id,
            },
        )