def test_filter_subquery(self):
        qs = Employee.objects.annotate(
            department_salary_rank=Window(
                Rank(), partition_by="department", order_by="-salary"
            )
        )
        msg = (
            "Referencing outer query window expression is not supported: "
            "department_salary_rank."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            qs.annotate(
                employee_name=Subquery(
                    Employee.objects.filter(
                        age=OuterRef("department_salary_rank")
                    ).values("name")[:1]
                )
            )