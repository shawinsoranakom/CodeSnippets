def test_tickets_1878_2939(self):
        self.assertEqual(Item.objects.values("creator").distinct().count(), 3)

        # Create something with a duplicate 'name' so that we can test
        # multi-column cases (which require some tricky SQL transformations
        # under the covers).
        xx = Item(name="four", created=self.time1, creator=self.a2, note=self.n1)
        xx.save()
        self.assertEqual(
            Item.objects.exclude(name="two")
            .values("creator", "name")
            .distinct()
            .count(),
            4,
        )
        self.assertEqual(
            (
                Item.objects.exclude(name="two")
                .extra(select={"foo": "%s"}, select_params=(1,))
                .values("creator", "name", "foo")
                .distinct()
                .count()
            ),
            4,
        )
        self.assertEqual(
            (
                Item.objects.exclude(name="two")
                .extra(select={"foo": "%s"}, select_params=(1,))
                .values("creator", "name")
                .distinct()
                .count()
            ),
            4,
        )
        xx.delete()