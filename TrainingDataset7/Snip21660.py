def test_nth_returns_null(self):
        """
        Find the nth row of the data set. None is returned since there are
        fewer than 20 rows in the test data.
        """
        qs = Employee.objects.annotate(
            nth_value=Window(
                expression=NthValue("salary", nth=20), order_by=F("salary").asc()
            )
        )
        self.assertEqual(
            list(qs.values_list("nth_value", flat=True).distinct()), [None]
        )