def test_update_fields_m2m(self):
        profile_boss = Profile.objects.create(name="Boss", salary=3000)
        e1 = Employee.objects.create(
            name="Sara", gender="F", employee_num=1, profile=profile_boss
        )
        a1 = Account.objects.create(num=1)
        a2 = Account.objects.create(num=2)
        e1.accounts.set([a1, a2])

        with self.assertRaisesMessage(ValueError, self.msg % "accounts"):
            e1.save(update_fields=["accounts"])