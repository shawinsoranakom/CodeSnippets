def test_slice_subquery_and_query(self):
        """
        Slice a query that has a sliced subquery
        """
        query = DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[0:2]
        ).order_by("id")[0:2]
        self.assertSequenceEqual([x.id for x in query], [3, 4])

        query = DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[1:3]
        ).order_by("id")[1:3]
        self.assertSequenceEqual([x.id for x in query], [3])

        query = DumbCategory.objects.filter(
            id__in=DumbCategory.objects.order_by("-id")[2:]
        ).order_by("id")[1:]
        self.assertSequenceEqual([x.id for x in query], [2])