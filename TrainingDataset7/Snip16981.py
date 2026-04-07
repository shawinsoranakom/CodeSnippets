def test_annotate_over_annotate(self):
        author = (
            Author.objects.annotate(age_alias=F("age"))
            .annotate(sum_age=Sum("age_alias"))
            .get(name="Adrian Holovaty")
        )

        other_author = Author.objects.annotate(sum_age=Sum("age")).get(
            name="Adrian Holovaty"
        )

        self.assertEqual(author.sum_age, other_author.sum_age)