def test_annotate_values_aggregate(self):
        alias_age = (
            Author.objects.annotate(age_alias=F("age"))
            .values(
                "age_alias",
            )
            .aggregate(sum_age=Sum("age_alias"))
        )

        age = Author.objects.values("age").aggregate(sum_age=Sum("age"))

        self.assertEqual(alias_age["sum_age"], age["sum_age"])