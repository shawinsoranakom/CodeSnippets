def test_o2o_cross_database_protection(self):
        """
        Operations that involve sharing FK objects across databases raise an
        error
        """
        # Create a user and profile on the default database
        alice = User.objects.db_manager("default").create_user(
            "alice", "alice@example.com"
        )

        # Create a user and profile on the other database
        bob = User.objects.db_manager("other").create_user("bob", "bob@example.com")

        # Set a one-to-one relation with an object from a different database
        alice_profile = UserProfile.objects.create(user=alice, flavor="chocolate")
        bob.userprofile = alice_profile

        # Database assignments of original objects haven't changed...
        self.assertEqual(alice._state.db, "default")
        self.assertEqual(alice_profile._state.db, "default")
        self.assertEqual(bob._state.db, "other")

        # ... but they will when the affected object is saved.
        bob.save()
        self.assertEqual(bob._state.db, "default")