def test_in_bulk(self):
        """
        Custom pks work with in_bulk, both for integer and non-integer types
        """
        emps = Employee.objects.in_bulk([123, 456])
        self.assertEqual(emps[123], self.dan)

        self.assertEqual(
            Business.objects.in_bulk(["Sears"]),
            {
                "Sears": self.business,
            },
        )