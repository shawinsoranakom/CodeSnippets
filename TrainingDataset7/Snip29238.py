def test_combine_isnull(self):
        item = Item.objects.create(title="Some Item")
        pv = PropertyValue.objects.create(label="Some Value")
        item.props.create(key="a", value=pv)
        item.props.create(key="b")  # value=NULL
        q1 = Q(props__key="a", props__value=pv)
        q2 = Q(props__key="b", props__value__isnull=True)

        # Each of these individually should return the item.
        self.assertEqual(Item.objects.get(q1), item)
        self.assertEqual(Item.objects.get(q2), item)

        # Logically, qs1 and qs2, and qs3 and qs4 should be the same.
        qs1 = Item.objects.filter(q1) & Item.objects.filter(q2)
        qs2 = Item.objects.filter(q2) & Item.objects.filter(q1)
        qs3 = Item.objects.filter(q1) | Item.objects.filter(q2)
        qs4 = Item.objects.filter(q2) | Item.objects.filter(q1)

        # Regression test for #15823.
        self.assertEqual(list(qs1), list(qs2))
        self.assertEqual(list(qs3), list(qs4))