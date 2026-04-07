def test_boolean_expression_combined_with_empty_Q(self):
        is_poc = Company.objects.filter(point_of_contact=OuterRef("pk"))
        self.gmbh.point_of_contact = self.max
        self.gmbh.save()
        tests = [
            Exists(is_poc) & Q(),
            Q() & Exists(is_poc),
            Exists(is_poc) | Q(),
            Q() | Exists(is_poc),
            Q(Exists(is_poc)) & Q(),
            Q() & Q(Exists(is_poc)),
            Q(Exists(is_poc)) | Q(),
            Q() | Q(Exists(is_poc)),
        ]
        for conditions in tests:
            with self.subTest(conditions):
                self.assertCountEqual(Employee.objects.filter(conditions), [self.max])