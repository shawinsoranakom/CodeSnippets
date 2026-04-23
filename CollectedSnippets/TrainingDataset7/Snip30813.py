def test_exclude_unsaved_object(self):
        company = Company.objects.create(name="Django")
        msg = "Model instances passed to related filters must be saved."
        with self.assertRaisesMessage(ValueError, msg):
            Employment.objects.exclude(employer=Company(name="unsaved"))
        with self.assertRaisesMessage(ValueError, msg):
            Employment.objects.exclude(employer__in=[company, Company(name="unsaved")])
        with self.assertRaisesMessage(ValueError, msg):
            StaffUser.objects.exclude(staff=Staff(name="unsaved"))