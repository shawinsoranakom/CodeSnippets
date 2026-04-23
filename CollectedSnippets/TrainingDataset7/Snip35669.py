def test_select_related_only_interaction(self):
        profile_boss = Profile.objects.create(name="Boss", salary=3000)
        e1 = Employee.objects.create(
            name="Sara", gender="F", employee_num=1, profile=profile_boss
        )
        e1 = (
            Employee.objects.only("profile__salary")
            .select_related("profile")
            .get(pk=e1.pk)
        )
        profile_boss.name = "Clerk"
        profile_boss.salary = 1000
        profile_boss.save()
        # The loaded salary of 3000 gets saved, the name of 'Clerk' isn't
        # overwritten.
        with self.assertNumQueries(1):
            e1.profile.save()
        reloaded_profile = Profile.objects.get(pk=profile_boss.pk)
        self.assertEqual(reloaded_profile.name, profile_boss.name)
        self.assertEqual(reloaded_profile.salary, 3000)