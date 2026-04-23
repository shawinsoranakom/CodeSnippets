def test_pickle_subquery_queryset_not_evaluated(self):
        group = Group.objects.create(name="group")
        Event.objects.create(title="event", group=group)
        groups = Group.objects.annotate(
            event_title=models.Subquery(
                Event.objects.filter(group_id=models.OuterRef("id")).values("title"),
            ),
        )
        list(groups)  # evaluate QuerySet.
        with self.assertNumQueries(0):
            self.assert_pickles(groups)