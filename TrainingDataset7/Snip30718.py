def test_ordered_subselect(self):
        "Subselects honor any manual ordering"
        query = DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[0:2]
        )
        self.assertEqual(set(query.values_list("id", flat=True)), {3, 4})

        query = DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[:2]
        )
        self.assertEqual(set(query.values_list("id", flat=True)), {3, 4})

        query = DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[1:2]
        )
        self.assertEqual(set(query.values_list("id", flat=True)), {3})

        query = DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[2:]
        )
        self.assertEqual(set(query.values_list("id", flat=True)), {1, 2})