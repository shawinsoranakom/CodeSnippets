def test_invalid_filter(self):
        msg = (
            "Heterogeneous disjunctive predicates against window functions are not "
            "implemented when performing conditional aggregation."
        )
        qs = Employee.objects.annotate(
            window=Window(Rank()),
            past_dept_cnt=Count("past_departments"),
        )
        with self.assertRaisesMessage(NotImplementedError, msg):
            list(qs.filter(Q(window=1) | Q(department="Accounting")))
        with self.assertRaisesMessage(NotImplementedError, msg):
            list(qs.exclude(window=1, department="Accounting"))