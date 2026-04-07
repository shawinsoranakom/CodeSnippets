def test_get(self):
        """
        Get can accept pk or the real attribute name
        """
        self.assertEqual(Employee.objects.get(pk=123), self.dan)
        self.assertEqual(Employee.objects.get(pk=456), self.fran)

        with self.assertRaises(Employee.DoesNotExist):
            Employee.objects.get(pk=42)

        # Use the name of the primary key, rather than pk.
        self.assertEqual(Employee.objects.get(employee_code=123), self.dan)