def test_order_by_tables(self):
        q1 = Item.objects.order_by("name")
        q2 = Item.objects.filter(id=self.i1.id)
        list(q2)
        combined_query = (q1 & q2).order_by("name").query
        self.assertEqual(
            len(
                [
                    t
                    for t in combined_query.alias_map
                    if combined_query.alias_refcount[t]
                ]
            ),
            1,
        )