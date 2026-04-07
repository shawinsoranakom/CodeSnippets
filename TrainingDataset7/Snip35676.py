def test_num_queries_inheritance(self):
        s = Employee.objects.create(name="Sara", gender="F")
        s.employee_num = 1
        s.name = "Emily"
        with self.assertNumQueries(1):
            s.save(update_fields=["employee_num"])
        s = Employee.objects.get(pk=s.pk)
        self.assertEqual(s.employee_num, 1)
        self.assertEqual(s.name, "Sara")
        s.employee_num = 2
        s.name = "Emily"
        with self.assertNumQueries(1):
            s.save(update_fields=["name"])
        s = Employee.objects.get(pk=s.pk)
        self.assertEqual(s.name, "Emily")
        self.assertEqual(s.employee_num, 1)
        # A little sanity check that we actually did updates...
        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(Person.objects.count(), 1)
        with self.assertNumQueries(2):
            s.save(update_fields=["name", "employee_num"])