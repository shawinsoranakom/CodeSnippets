def test_trim(self):
        Author.objects.create(name="  John ", alias="j")
        Author.objects.create(name="Rhonda", alias="r")
        authors = Author.objects.annotate(
            ltrim=LTrim("name"),
            rtrim=RTrim("name"),
            trim=Trim("name"),
        )
        self.assertQuerySetEqual(
            authors.order_by("alias"),
            [
                ("John ", "  John", "John"),
                ("Rhonda", "Rhonda", "Rhonda"),
            ],
            lambda a: (a.ltrim, a.rtrim, a.trim),
        )