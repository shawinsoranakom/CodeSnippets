def test_range_lookup_allows_F_expressions_and_expressions_for_dates(self):
        start = datetime.datetime(2016, 2, 3, 15, 0, 0)
        end = datetime.datetime(2016, 2, 5, 15, 0, 0)
        experiment_1 = Experiment.objects.create(
            name="Integrity testing",
            assigned=start.date(),
            start=start,
            end=end,
            completed=end.date(),
            estimated_time=end - start,
        )
        experiment_2 = Experiment.objects.create(
            name="Taste testing",
            assigned=start.date(),
            start=start,
            end=end,
            completed=end.date(),
            estimated_time=end - start,
        )
        r1 = Result.objects.create(
            experiment=experiment_1,
            result_time=datetime.datetime(2016, 2, 4, 15, 0, 0),
        )
        Result.objects.create(
            experiment=experiment_1,
            result_time=datetime.datetime(2016, 3, 10, 2, 0, 0),
        )
        Result.objects.create(
            experiment=experiment_2,
            result_time=datetime.datetime(2016, 1, 8, 5, 0, 0),
        )
        tests = [
            # Datetimes.
            ([F("experiment__start"), F("experiment__end")], "result_time__range"),
            # Dates.
            (
                [F("experiment__start__date"), F("experiment__end__date")],
                "result_time__date__range",
            ),
        ]
        for within_experiment_time, lookup in tests:
            with self.subTest(lookup=lookup):
                queryset = Result.objects.filter(**{lookup: within_experiment_time})
                self.assertSequenceEqual(queryset, [r1])