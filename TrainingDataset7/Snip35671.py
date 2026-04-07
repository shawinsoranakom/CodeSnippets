def test_update_fields_inheritance(self):
        profile_boss = Profile.objects.create(name="Boss", salary=3000)
        profile_receptionist = Profile.objects.create(name="Receptionist", salary=1000)
        e1 = Employee.objects.create(
            name="Sara", gender="F", employee_num=1, profile=profile_boss
        )

        e1.name = "Ian"
        e1.gender = "M"
        e1.save(update_fields=["name"])

        e2 = Employee.objects.get(pk=e1.pk)
        self.assertEqual(e2.name, "Ian")
        self.assertEqual(e2.gender, "F")
        self.assertEqual(e2.profile, profile_boss)

        e2.profile = profile_receptionist
        e2.name = "Sara"
        e2.save(update_fields=["profile"])

        e3 = Employee.objects.get(pk=e1.pk)
        self.assertEqual(e3.name, "Ian")
        self.assertEqual(e3.profile, profile_receptionist)

        with self.assertNumQueries(1):
            e3.profile = profile_boss
            e3.save(update_fields=["profile_id"])

        e4 = Employee.objects.get(pk=e3.pk)
        self.assertEqual(e4.profile, profile_boss)
        self.assertEqual(e4.profile_id, profile_boss.pk)