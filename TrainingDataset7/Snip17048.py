def test_string_agg_jsonfield_order_by(self):
        Employee.objects.bulk_create(
            [
                Employee(work_day_preferences={"Monday": "morning"}),
                Employee(work_day_preferences={"Monday": "afternoon"}),
            ]
        )
        values = Employee.objects.aggregate(
            stringagg=StringAgg(
                KeyTextTransform("Monday", "work_day_preferences"),
                delimiter=Value(","),
                order_by=KeyTextTransform(
                    "Monday",
                    "work_day_preferences",
                ),
                output_field=CharField(),
            ),
        )
        self.assertEqual(values, {"stringagg": "afternoon,morning"})