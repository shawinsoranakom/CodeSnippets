def test_values_extra(self):
        # The values() method works with "extra" fields specified in
        # extra(select).
        self.assertSequenceEqual(
            Article.objects.extra(select={"id_plus_one": "id + 1"}).values(
                "id", "id_plus_one"
            ),
            [
                {"id": self.a5.id, "id_plus_one": self.a5.id + 1},
                {"id": self.a6.id, "id_plus_one": self.a6.id + 1},
                {"id": self.a4.id, "id_plus_one": self.a4.id + 1},
                {"id": self.a2.id, "id_plus_one": self.a2.id + 1},
                {"id": self.a3.id, "id_plus_one": self.a3.id + 1},
                {"id": self.a7.id, "id_plus_one": self.a7.id + 1},
                {"id": self.a1.id, "id_plus_one": self.a1.id + 1},
            ],
        )
        data = {
            "id_plus_one": "id+1",
            "id_plus_two": "id+2",
            "id_plus_three": "id+3",
            "id_plus_four": "id+4",
            "id_plus_five": "id+5",
            "id_plus_six": "id+6",
            "id_plus_seven": "id+7",
            "id_plus_eight": "id+8",
        }
        self.assertSequenceEqual(
            Article.objects.filter(id=self.a1.id).extra(select=data).values(*data),
            [
                {
                    "id_plus_one": self.a1.id + 1,
                    "id_plus_two": self.a1.id + 2,
                    "id_plus_three": self.a1.id + 3,
                    "id_plus_four": self.a1.id + 4,
                    "id_plus_five": self.a1.id + 5,
                    "id_plus_six": self.a1.id + 6,
                    "id_plus_seven": self.a1.id + 7,
                    "id_plus_eight": self.a1.id + 8,
                }
            ],
        )