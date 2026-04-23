def test_create_new_instance_with_pk_equals_none(self):
        p1 = Profile.objects.create(username="john")
        p2 = User.objects.get(pk=p1.user_ptr_id).profile
        # Create a new profile by setting pk = None.
        p2.pk = None
        p2.user_ptr_id = None
        p2.username = "bill"
        p2.save()
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(User.objects.get(pk=p1.user_ptr_id).username, "john")