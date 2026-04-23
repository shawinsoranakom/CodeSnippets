def test_pickle_filteredrelation(self):
        group = Group.objects.create(name="group")
        event_1 = Event.objects.create(title="Big event", group=group)
        event_2 = Event.objects.create(title="Small event", group=group)
        Happening.objects.bulk_create(
            [
                Happening(event=event_1, number1=5),
                Happening(event=event_2, number1=3),
            ]
        )
        groups = Group.objects.annotate(
            big_events=models.FilteredRelation(
                "event",
                condition=models.Q(event__title__startswith="Big"),
            ),
        ).annotate(sum_number=models.Sum("big_events__happening__number1"))
        groups_query = pickle.loads(pickle.dumps(groups.query))
        groups = Group.objects.all()
        groups.query = groups_query
        self.assertEqual(groups.get().sum_number, 5)