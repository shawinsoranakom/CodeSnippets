def test_pickle_exists_queryset_still_usable(self):
        group = Group.objects.create(name="group")
        Event.objects.create(title="event", group=group)
        groups = Group.objects.annotate(
            has_event=models.Exists(
                Event.objects.filter(group_id=models.OuterRef("id")),
            ),
        )
        groups2 = pickle.loads(pickle.dumps(groups))
        self.assertSequenceEqual(groups2.filter(has_event=True), [group])