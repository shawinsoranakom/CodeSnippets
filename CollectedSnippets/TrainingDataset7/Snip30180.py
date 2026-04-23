def test_prefetch_queryset_child_class(self):
        employee = SelfDirectedEmployee.objects.create(name="Foo")
        employee.boss = employee
        employee.save()
        with self.assertNumQueries(2):
            retrieved_employee = SelfDirectedEmployee.objects.prefetch_related(
                Prefetch("boss", SelfDirectedEmployee.objects.all())
            ).get()
        with self.assertNumQueries(0):
            self.assertEqual(retrieved_employee, employee)
            self.assertEqual(retrieved_employee.boss, retrieved_employee)