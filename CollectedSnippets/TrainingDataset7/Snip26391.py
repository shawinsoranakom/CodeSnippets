def test_related_object(self):
        public_school = School.objects.create(is_public=True)
        public_student = Student.objects.create(school=public_school)

        private_school = School.objects.create(is_public=False)
        private_student = Student.objects.create(school=private_school)

        # Only one school is available via all() due to the custom default
        # manager.
        self.assertSequenceEqual(School.objects.all(), [public_school])

        self.assertEqual(public_student.school, public_school)

        # Make sure the base manager is used so that a student can still access
        # its related school even if the default manager doesn't normally
        # allow it.
        self.assertEqual(private_student.school, private_school)

        School._meta.base_manager_name = "objects"
        School._meta._expire_cache()
        try:
            private_student = Student.objects.get(pk=private_student.pk)
            with self.assertRaises(School.DoesNotExist):
                private_student.school
        finally:
            School._meta.base_manager_name = None
            School._meta._expire_cache()