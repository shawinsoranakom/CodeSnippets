def test_order_by_annotation(self):
        authors = Author.objects.annotate(other_age=F("age")).order_by("other_age")
        self.assertQuerySetEqual(
            authors,
            [
                25,
                29,
                29,
                34,
                35,
                37,
                45,
                46,
                57,
            ],
            lambda a: a.other_age,
        )