def test_chaining_annotation_filter_with_m2m(self):
        qs = (
            Author.objects.filter(
                name="Adrian Holovaty",
                friends__age=35,
            )
            .annotate(
                jacob_name=F("friends__name"),
            )
            .filter(
                friends__age=29,
            )
            .annotate(
                james_name=F("friends__name"),
            )
            .values("jacob_name", "james_name")
        )
        self.assertCountEqual(
            qs,
            [{"jacob_name": "Jacob Kaplan-Moss", "james_name": "James Bennett"}],
        )