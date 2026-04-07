def test_date_case_subtraction(self):
        queryset = Experiment.objects.annotate(
            date_case=Case(
                When(Q(name="e0"), then=F("completed")),
                output_field=DateField(),
            ),
            completed_value=Value(
                self.e0.completed,
                output_field=DateField(),
            ),
            difference=F("date_case") - F("completed_value"),
        ).filter(difference=datetime.timedelta())
        self.assertEqual(queryset.get(), self.e0)