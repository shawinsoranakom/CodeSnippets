def test_pickle_boolean_expression_in_Q__queryset(self):
        group = Group.objects.create(name="group")
        Event.objects.create(title="event", group=group)
        groups = Group.objects.filter(
            models.Q(
                models.Exists(
                    Event.objects.filter(group_id=models.OuterRef("id")),
                )
            ),
        )
        groups2 = pickle.loads(pickle.dumps(groups))
        self.assertSequenceEqual(groups2, [group])