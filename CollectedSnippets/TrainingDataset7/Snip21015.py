def test_only_values_does_not_defer(self):
        self.assertEqual(
            Primary.objects.only("name").values()[0],
            {
                "id": self.p1.id,
                "name": "p1",
                "value": "xx",
                "related_id": self.s1.id,
            },
        )