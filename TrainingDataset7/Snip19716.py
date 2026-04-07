def test_totally_ordered(self):
        """
        QuerySet.totally_ordered returns True when ordering by all fields of a
        composite primary key and False when ordering by a subset.
        """
        qs_ordered = Token.objects.order_by("tenant_id", "id")
        self.assertIs(qs_ordered.totally_ordered, True)
        qs_partial = Token.objects.order_by("tenant_id")
        self.assertIs(qs_partial.totally_ordered, False)