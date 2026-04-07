def test_update_fields_inheritance_defer(self):
        profile_boss = Profile.objects.create(name="Boss", salary=3000)
        e1 = Employee.objects.create(
            name="Sara", gender="F", employee_num=1, profile=profile_boss
        )
        e1 = Employee.objects.only("name").get(pk=e1.pk)
        e1.name = "Linda"
        with self.assertNumQueries(1):
            e1.save()
        self.assertEqual(Employee.objects.get(pk=e1.pk).name, "Linda")