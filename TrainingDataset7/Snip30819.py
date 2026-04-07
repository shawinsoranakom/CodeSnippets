def test_exclude_with_q_is_equal_to_plain_exclude(self):
        """
        Using exclude(condition) and exclude(Q(condition)) should
        yield the same QuerySet
        """
        self.assertEqual(
            list(Order.objects.exclude(items__status=1).distinct()),
            list(Order.objects.exclude(Q(items__status=1)).distinct()),
        )