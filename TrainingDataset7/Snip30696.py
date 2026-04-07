def test_multiple_columns_with_the_same_name_slice(self):
        self.assertEqual(
            list(
                Tag.objects.order_by("name").values_list("name", "category__name")[:2]
            ),
            [("t1", "Generic"), ("t2", "Generic")],
        )
        self.assertSequenceEqual(
            Tag.objects.order_by("name").select_related("category")[:2],
            [self.t1, self.t2],
        )
        self.assertEqual(
            list(Tag.objects.order_by("-name").values_list("name", "parent__name")[:2]),
            [("t5", "t3"), ("t4", "t3")],
        )
        self.assertSequenceEqual(
            Tag.objects.order_by("-name").select_related("parent")[:2],
            [self.t5, self.t4],
        )