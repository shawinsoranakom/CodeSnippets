def test_expressions_range_lookups_join_choice(self):
        midpoint = datetime.time(13, 0)
        t1 = Time.objects.create(time=datetime.time(12, 0))
        t2 = Time.objects.create(time=datetime.time(14, 0))
        s1 = SimulationRun.objects.create(start=t1, end=t2, midpoint=midpoint)
        SimulationRun.objects.create(start=t1, end=None, midpoint=midpoint)
        SimulationRun.objects.create(start=None, end=t2, midpoint=midpoint)
        SimulationRun.objects.create(start=None, end=None, midpoint=midpoint)

        queryset = SimulationRun.objects.filter(
            midpoint__range=[F("start__time"), F("end__time")]
        )
        self.assertSequenceEqual(queryset, [s1])
        for alias in queryset.query.alias_map.values():
            if isinstance(alias, Join):
                self.assertEqual(alias.join_type, constants.INNER)

        queryset = SimulationRun.objects.exclude(
            midpoint__range=[F("start__time"), F("end__time")]
        )
        self.assertQuerySetEqual(queryset, [], ordered=False)
        for alias in queryset.query.alias_map.values():
            if isinstance(alias, Join):
                self.assertEqual(alias.join_type, constants.LOUTER)