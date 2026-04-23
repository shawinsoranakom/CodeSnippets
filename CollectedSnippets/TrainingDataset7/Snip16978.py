def test_aggregate_over_complex_annotation(self):
        qs = Author.objects.annotate(combined_ages=Sum(F("age") + F("friends__age")))

        age = qs.aggregate(max_combined_age=Max("combined_ages"))
        self.assertEqual(age["max_combined_age"], 176)

        age = qs.aggregate(max_combined_age_doubled=Max("combined_ages") * 2)
        self.assertEqual(age["max_combined_age_doubled"], 176 * 2)

        age = qs.aggregate(
            max_combined_age_doubled=Max("combined_ages") + Max("combined_ages")
        )
        self.assertEqual(age["max_combined_age_doubled"], 176 * 2)

        age = qs.aggregate(
            max_combined_age_doubled=Max("combined_ages") + Max("combined_ages"),
            sum_combined_age=Sum("combined_ages"),
        )
        self.assertEqual(age["max_combined_age_doubled"], 176 * 2)
        self.assertEqual(age["sum_combined_age"], 954)

        age = qs.aggregate(
            max_combined_age_doubled=Max("combined_ages") + Max("combined_ages"),
            sum_combined_age_doubled=Sum("combined_ages") + Sum("combined_ages"),
        )
        self.assertEqual(age["max_combined_age_doubled"], 176 * 2)
        self.assertEqual(age["sum_combined_age_doubled"], 954 * 2)