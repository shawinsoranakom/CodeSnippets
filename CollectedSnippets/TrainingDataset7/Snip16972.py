def test_annotation_expressions(self):
        authors = Author.objects.annotate(
            combined_ages=Sum(F("age") + F("friends__age"))
        ).order_by("name")
        authors2 = Author.objects.annotate(
            combined_ages=Sum("age") + Sum("friends__age")
        ).order_by("name")
        for qs in (authors, authors2):
            self.assertQuerySetEqual(
                qs,
                [
                    ("Adrian Holovaty", 132),
                    ("Brad Dayley", None),
                    ("Jacob Kaplan-Moss", 129),
                    ("James Bennett", 63),
                    ("Jeffrey Forcier", 128),
                    ("Paul Bissex", 120),
                    ("Peter Norvig", 103),
                    ("Stuart Russell", 103),
                    ("Wesley J. Chun", 176),
                ],
                lambda a: (a.name, a.combined_ages),
            )