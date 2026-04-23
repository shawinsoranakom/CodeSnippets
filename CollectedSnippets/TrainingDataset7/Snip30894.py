def test_filter_rejects_invalid_arguments(self):
        school = School.objects.create()
        msg = "The following kwargs are invalid: '_connector', '_negated'"
        with self.assertRaisesMessage(TypeError, msg):
            School.objects.filter(pk=school.pk, _negated=True, _connector="evil")