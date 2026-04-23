def test_filter_unsaved_object(self):
        msg = "Model instances passed to related filters must be saved."
        company = Company.objects.create(name="Django")
        with self.assertRaisesMessage(ValueError, msg):
            Employment.objects.filter(employer=Company(name="unsaved"))
        with self.assertRaisesMessage(ValueError, msg):
            Employment.objects.filter(employer__in=[company, Company(name="unsaved")])
        with self.assertRaisesMessage(ValueError, msg):
            StaffUser.objects.filter(staff=Staff(name="unsaved"))