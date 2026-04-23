def test_fields_cache_reset_on_copy(self):
        department1 = Department.objects.create(id=1, name="department1")
        department2 = Department.objects.create(id=2, name="department2")
        worker1 = Worker.objects.create(name="worker", department=department1)
        worker2 = copy.copy(worker1)

        self.assertEqual(worker2.department, department1)
        # Changing related fields doesn't mutate the base object.
        worker2.department = department2
        self.assertEqual(worker2.department, department2)
        self.assertEqual(worker1.department, department1)