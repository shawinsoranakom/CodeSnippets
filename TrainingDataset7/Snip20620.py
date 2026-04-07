def test_case_sensitive(self):
        qs = Author.objects.annotate(
            same_name=Replace(F("name"), Value("r. r."), Value(""))
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("George R. R. Martin", "George R. R. Martin"),
                ("J. R. R. Tolkien", "J. R. R. Tolkien"),
            ],
            transform=lambda x: (x.name, x.same_name),
            ordered=False,
        )