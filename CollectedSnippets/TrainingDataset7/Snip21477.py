def test_date_subtraction(self):
        queryset = Experiment.objects.annotate(
            completion_duration=F("completed") - F("assigned"),
        )

        at_least_5_days = {
            e.name
            for e in queryset.filter(
                completion_duration__gte=datetime.timedelta(days=5)
            )
        }
        self.assertEqual(at_least_5_days, {"e3", "e4", "e5"})

        at_least_120_days = {
            e.name
            for e in queryset.filter(
                completion_duration__gte=datetime.timedelta(days=120)
            )
        }
        self.assertEqual(at_least_120_days, {"e5"})

        less_than_5_days = {
            e.name
            for e in queryset.filter(completion_duration__lt=datetime.timedelta(days=5))
        }
        self.assertEqual(less_than_5_days, {"e0", "e1", "e2"})

        queryset = Experiment.objects.annotate(
            difference=F("completed") - Value(None, output_field=DateField()),
        )
        self.assertIsNone(queryset.first().difference)

        queryset = Experiment.objects.annotate(
            shifted=ExpressionWrapper(
                F("completed") - Value(None, output_field=DurationField()),
                output_field=DateField(),
            )
        )
        self.assertIsNone(queryset.first().shifted)