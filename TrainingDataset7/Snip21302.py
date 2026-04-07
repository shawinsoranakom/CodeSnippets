def test_distinct_not_implemented_checks(self):
        # distinct + annotate not allowed
        msg = "annotate() + distinct(fields) is not implemented."
        with self.assertRaisesMessage(NotImplementedError, msg):
            Celebrity.objects.annotate(Max("id")).distinct("id")[0]
        with self.assertRaisesMessage(NotImplementedError, msg):
            Celebrity.objects.distinct("id").annotate(Max("id"))[0]

        # However this check is done only when the query executes, so you
        # can use distinct() to remove the fields before execution.
        Celebrity.objects.distinct("id").annotate(Max("id")).distinct()[0]
        # distinct + aggregate not allowed
        msg = "aggregate() + distinct(fields) not implemented."
        with self.assertRaisesMessage(NotImplementedError, msg):
            Celebrity.objects.distinct("id").aggregate(Max("id"))