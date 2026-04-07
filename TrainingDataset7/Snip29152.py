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
        alice_profile = UserProfile.objects.using("default").create(
            user=alice, flavor="chocolate"
        )
        msg = (
            'Cannot assign "%r": the current database router prevents this '
            "relation." % alice_profile
        )
        with self.assertRaisesMessage(ValueError, msg):
            bob.userprofile = alice_profile

        # BUT! if you assign a FK object when the base object hasn't
        # been saved yet, you implicitly assign the database for the
        # base object.
        bob_profile = UserProfile.objects.using("other").create(
            user=bob, flavor="crunchy frog"
        )

        new_bob_profile = UserProfile(flavor="spring surprise")

        # assigning a profile requires an explicit pk as the object isn't saved
        charlie = User(pk=51, username="charlie", email="charlie@example.com")
        charlie.set_unusable_password()

        # initially, no db assigned
        self.assertIsNone(new_bob_profile._state.db)
        self.assertIsNone(charlie._state.db)

        # old object comes from 'other', so the new object is set to use
        # 'other'...
        new_bob_profile.user = bob
        charlie.userprofile = bob_profile
        self.assertEqual(new_bob_profile._state.db, "other")
        self.assertEqual(charlie._state.db, "other")

        # ... but it isn't saved yet
        self.assertEqual(
            list(User.objects.using("other").values_list("username", flat=True)),
            ["bob"],
        )
        self.assertEqual(
            list(UserProfile.objects.using("other").values_list("flavor", flat=True)),
            ["crunchy frog"],
        )

        # When saved (no using required), new objects goes to 'other'
        charlie.save()
        bob_profile.save()
        new_bob_profile.save()
        self.assertEqual(
            list(User.objects.using("default").values_list("username", flat=True)),
            ["alice"],
        )
        self.assertEqual(
            list(User.objects.using("other").values_list("username", flat=True)),
            ["bob", "charlie"],
        )
        self.assertEqual(
            list(UserProfile.objects.using("default").values_list("flavor", flat=True)),
            ["chocolate"],
        )
        self.assertEqual(
            list(UserProfile.objects.using("other").values_list("flavor", flat=True)),
            ["crunchy frog", "spring surprise"],
        )

        # This also works if you assign the O2O relation in the constructor
        denise = User.objects.db_manager("other").create_user(
            "denise", "denise@example.com"
        )
        denise_profile = UserProfile(flavor="tofu", user=denise)

        self.assertEqual(denise_profile._state.db, "other")
        # ... but it isn't saved yet
        self.assertEqual(
            list(UserProfile.objects.using("default").values_list("flavor", flat=True)),
            ["chocolate"],
        )
        self.assertEqual(
            list(UserProfile.objects.using("other").values_list("flavor", flat=True)),
            ["crunchy frog", "spring surprise"],
        )

        # When saved, the new profile goes to 'other'
        denise_profile.save()
        self.assertEqual(
            list(UserProfile.objects.using("default").values_list("flavor", flat=True)),
            ["chocolate"],
        )
        self.assertEqual(
            list(UserProfile.objects.using("other").values_list("flavor", flat=True)),
            ["crunchy frog", "spring surprise", "tofu"],
        )