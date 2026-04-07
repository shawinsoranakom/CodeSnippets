def test_annotation_in_f_grouped_by_annotation(self):
        qs = (
            Publisher.objects.annotate(multiplier=Value(3))
            # group by option => sum of value * multiplier
            .values("name")
            .annotate(multiplied_value_sum=Sum(F("multiplier") * F("num_awards")))
            .order_by()
        )
        self.assertCountEqual(
            qs,
            [
                {"multiplied_value_sum": 9, "name": "Apress"},
                {"multiplied_value_sum": 0, "name": "Jonno's House of Books"},
                {"multiplied_value_sum": 27, "name": "Morgan Kaufmann"},
                {"multiplied_value_sum": 21, "name": "Prentice Hall"},
                {"multiplied_value_sum": 3, "name": "Sams"},
            ],
        )