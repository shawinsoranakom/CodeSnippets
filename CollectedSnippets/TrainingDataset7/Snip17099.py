def test_annotate_select_related(self):
        # Regression for #10127 - Empty select_related() works with annotate
        qs = (
            Book.objects.filter(rating__lt=4.5)
            .select_related()
            .annotate(Avg("authors__age"))
            .order_by("name")
        )
        self.assertQuerySetEqual(
            qs,
            [
                (
                    "Artificial Intelligence: A Modern Approach",
                    51.5,
                    "Prentice Hall",
                    "Peter Norvig",
                ),
                ("Practical Django Projects", 29.0, "Apress", "James Bennett"),
                (
                    "Python Web Development with Django",
                    Approximate(30.333, places=2),
                    "Prentice Hall",
                    "Jeffrey Forcier",
                ),
                ("Sams Teach Yourself Django in 24 Hours", 45.0, "Sams", "Brad Dayley"),
            ],
            lambda b: (b.name, b.authors__age__avg, b.publisher.name, b.contact.name),
        )