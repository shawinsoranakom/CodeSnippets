def test_annotations_within_subquery(self):
        Company.objects.filter(num_employees__lt=50).update(
            ceo=Employee.objects.get(firstname="Frank")
        )
        inner = (
            Company.objects.filter(ceo=OuterRef("pk"))
            .values("ceo")
            .annotate(total_employees=Sum("num_employees"))
            .values("total_employees")
        )
        outer = Employee.objects.annotate(total_employees=Subquery(inner)).filter(
            salary__lte=Subquery(inner)
        )
        self.assertSequenceEqual(
            outer.order_by("-total_employees").values("salary", "total_employees"),
            [
                {"salary": 10, "total_employees": 2300},
                {"salary": 20, "total_employees": 35},
            ],
        )