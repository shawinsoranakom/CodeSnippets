def test_choices(self):
        field = Recipe._meta.get_field("ingredients")
        self.assertEqual(
            [choice[0] for choice in field.get_choices(include_blank=False)],
            ["pea", "potato", "tomato"],
        )