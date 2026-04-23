def test_range_lookup_namedtuple(self):
        EmployeeRange = namedtuple("EmployeeRange", ["minimum", "maximum"])
        qs = Company.objects.filter(
            num_employees__range=EmployeeRange(minimum=51, maximum=100),
        )
        self.assertSequenceEqual(qs, [self.c99300])