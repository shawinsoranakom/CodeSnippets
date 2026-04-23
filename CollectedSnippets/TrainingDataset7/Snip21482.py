def test_datetime_subtraction(self):
        under_estimate = [
            e.name
            for e in Experiment.objects.filter(estimated_time__gt=F("end") - F("start"))
        ]
        self.assertEqual(under_estimate, ["e2"])

        over_estimate = [
            e.name
            for e in Experiment.objects.filter(estimated_time__lt=F("end") - F("start"))
        ]
        self.assertEqual(over_estimate, ["e4"])

        queryset = Experiment.objects.annotate(
            difference=F("start") - Value(None, output_field=DateTimeField()),
        )
        self.assertIsNone(queryset.first().difference)

        queryset = Experiment.objects.annotate(
            shifted=ExpressionWrapper(
                F("start") - Value(None, output_field=DurationField()),
                output_field=DateTimeField(),
            )
        )
        self.assertIsNone(queryset.first().shifted)