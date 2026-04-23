def test_durationfield_add(self):
        zeros = [
            e.name
            for e in Experiment.objects.filter(start=F("start") + F("estimated_time"))
        ]
        self.assertEqual(zeros, ["e0"])

        end_less = [
            e.name
            for e in Experiment.objects.filter(end__lt=F("start") + F("estimated_time"))
        ]
        self.assertEqual(end_less, ["e2"])

        delta_math = [
            e.name
            for e in Experiment.objects.filter(
                end__gte=F("start") + F("estimated_time") + datetime.timedelta(hours=1)
            )
        ]
        self.assertEqual(delta_math, ["e4"])

        queryset = Experiment.objects.annotate(
            shifted=ExpressionWrapper(
                F("start") + Value(None, output_field=DurationField()),
                output_field=DateTimeField(),
            )
        )
        self.assertIsNone(queryset.first().shifted)