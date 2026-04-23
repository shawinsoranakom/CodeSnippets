def test_replace_with_empty_string(self):
        qs = Author.objects.annotate(
            without_middlename=Replace(F("name"), Value("R. R. "), Value("")),
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("George R. R. Martin", "George Martin"),
                ("J. R. R. Tolkien", "J. Tolkien"),
            ],
            transform=lambda x: (x.name, x.without_middlename),
            ordered=False,
        )