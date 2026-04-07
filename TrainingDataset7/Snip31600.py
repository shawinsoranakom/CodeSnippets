def test_missing_reverse(self):
        """
        Ticket #13839: select_related() should NOT cache None
        for missing objects on a reverse 1-1 relation.
        """
        with self.assertNumQueries(1):
            user = User.objects.select_related("userprofile").get(username="bob")
            with self.assertRaises(UserProfile.DoesNotExist):
                user.userprofile