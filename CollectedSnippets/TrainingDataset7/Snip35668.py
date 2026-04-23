def test_update_fields_fk_defer(self):
        profile_boss = Profile.objects.create(name="Boss", salary=3000)
        profile_receptionist = Profile.objects.create(name="Receptionist", salary=1000)
        e1 = Employee.objects.create(
            name="Sara", gender="F", employee_num=1, profile=profile_boss
        )
        e1 = Employee.objects.only("profile").get(pk=e1.pk)
        e1.profile = profile_receptionist
        with self.assertNumQueries(1):
            e1.save()
        self.assertEqual(Employee.objects.get(pk=e1.pk).profile, profile_receptionist)
        e1.profile_id = profile_boss.pk
        with self.assertNumQueries(1):
            e1.save()
        self.assertEqual(Employee.objects.get(pk=e1.pk).profile, profile_boss)