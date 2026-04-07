def test_o2o_separation(self):
        "OneToOne fields are constrained to a single database"
        # Create a user and profile on the default database
        alice = User.objects.db_manager("default").create_user(
            "alice", "alice@example.com"
        )
        alice_profile = UserProfile.objects.using("default").create(
            user=alice, flavor="chocolate"
        )

        # Create a user and profile on the other database
        bob = User.objects.db_manager("other").create_user("bob", "bob@example.com")
        bob_profile = UserProfile.objects.using("other").create(
            user=bob, flavor="crunchy frog"
        )

        # Retrieve related objects; queries should be database constrained
        alice = User.objects.using("default").get(username="alice")
        self.assertEqual(alice.userprofile.flavor, "chocolate")

        bob = User.objects.using("other").get(username="bob")
        self.assertEqual(bob.userprofile.flavor, "crunchy frog")

        # Queries work across joins
        self.assertEqual(
            list(
                User.objects.using("default")
                .filter(userprofile__flavor="chocolate")
                .values_list("username", flat=True)
            ),
            ["alice"],
        )
        self.assertEqual(
            list(
                User.objects.using("other")
                .filter(userprofile__flavor="chocolate")
                .values_list("username", flat=True)
            ),
            [],
        )

        self.assertEqual(
            list(
                User.objects.using("default")
                .filter(userprofile__flavor="crunchy frog")
                .values_list("username", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                User.objects.using("other")
                .filter(userprofile__flavor="crunchy frog")
                .values_list("username", flat=True)
            ),
            ["bob"],
        )

        # Reget the objects to clear caches
        alice_profile = UserProfile.objects.using("default").get(flavor="chocolate")
        bob_profile = UserProfile.objects.using("other").get(flavor="crunchy frog")

        # Retrieve related object by descriptor. Related objects should be
        # database-bound.
        self.assertEqual(alice_profile.user.username, "alice")
        self.assertEqual(bob_profile.user.username, "bob")