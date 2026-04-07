def test_related_object(self):
        public_school = School.objects.create(is_public=True)
        public_director = Director.objects.create(school=public_school, is_temp=False)

        private_school = School.objects.create(is_public=False)
        private_director = Director.objects.create(school=private_school, is_temp=True)

        # Only one school is available via all() due to the custom default
        # manager.
        self.assertSequenceEqual(School.objects.all(), [public_school])

        # Only one director is available via all() due to the custom default
        # manager.
        self.assertSequenceEqual(Director.objects.all(), [public_director])

        self.assertEqual(public_director.school, public_school)
        self.assertEqual(public_school.director, public_director)

        # Make sure the base manager is used so that the related objects
        # is still accessible even if the default manager doesn't normally
        # allow it.
        self.assertEqual(private_director.school, private_school)

        # Make sure the base manager is used so that an student can still
        # access its related school even if the default manager doesn't
        # normally allow it.
        self.assertEqual(private_school.director, private_director)

        School._meta.base_manager_name = "objects"
        School._meta._expire_cache()
        try:
            private_director = Director._base_manager.get(pk=private_director.pk)
            with self.assertRaises(School.DoesNotExist):
                private_director.school
        finally:
            School._meta.base_manager_name = None
            School._meta._expire_cache()

        Director._meta.base_manager_name = "objects"
        Director._meta._expire_cache()
        try:
            private_school = School._base_manager.get(pk=private_school.pk)
            with self.assertRaises(Director.DoesNotExist):
                private_school.director
        finally:
            Director._meta.base_manager_name = None
            Director._meta._expire_cache()