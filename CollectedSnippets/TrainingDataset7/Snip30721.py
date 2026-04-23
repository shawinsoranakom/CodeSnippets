def test_sliced_delete(self):
        "Delete queries can safely contain sliced subqueries"
        DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[0:1]
        ).delete()
        self.assertEqual(
            set(DumbCategory.objects.values_list("id", flat=True)), {1, 2, 3}
        )

        DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[1:2]
        ).delete()
        self.assertEqual(set(DumbCategory.objects.values_list("id", flat=True)), {1, 3})

        DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[1:]
        ).delete()
        self.assertEqual(set(DumbCategory.objects.values_list("id", flat=True)), {3})