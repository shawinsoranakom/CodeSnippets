def test_update_fields_inheritance_with_proxy_model(self):
        profile_boss = Profile.objects.create(name="Boss", salary=3000)
        profile_receptionist = Profile.objects.create(name="Receptionist", salary=1000)
        e1 = ProxyEmployee.objects.create(
            name="Sara", gender="F", employee_num=1, profile=profile_boss
        )

        e1.name = "Ian"
        e1.gender = "M"
        e1.save(update_fields=["name"])

        e2 = ProxyEmployee.objects.get(pk=e1.pk)
        self.assertEqual(e2.name, "Ian")
        self.assertEqual(e2.gender, "F")
        self.assertEqual(e2.profile, profile_boss)

        e2.profile = profile_receptionist
        e2.name = "Sara"
        e2.save(update_fields=["profile"])

        e3 = ProxyEmployee.objects.get(pk=e1.pk)
        self.assertEqual(e3.name, "Ian")
        self.assertEqual(e3.profile, profile_receptionist)