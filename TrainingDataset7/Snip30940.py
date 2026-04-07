def test_pickle_exists_kwargs_queryset_not_evaluated(self):
        group = Group.objects.create(name="group")
        Event.objects.create(title="event", group=group)
        groups = Group.objects.annotate(
            has_event=models.Exists(
                queryset=Event.objects.filter(group_id=models.OuterRef("id")),
            ),
        )
        list(groups)  # evaluate QuerySet.
        with self.assertNumQueries(0):
            self.assert_pickles(groups)