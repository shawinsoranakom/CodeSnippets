def test_boolean_expression_in_Q(self):
        is_poc = Company.objects.filter(point_of_contact=OuterRef("pk"))
        self.gmbh.point_of_contact = self.max
        self.gmbh.save()
        self.assertCountEqual(Employee.objects.filter(Q(Exists(is_poc))), [self.max])