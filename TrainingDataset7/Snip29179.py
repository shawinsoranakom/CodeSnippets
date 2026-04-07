def test_auth_manager(self):
        "The methods on the auth manager obey database hints"
        # Create one user using default allocation policy
        User.objects.create_user("alice", "alice@example.com")

        # Create another user, explicitly specifying the database
        User.objects.db_manager("default").create_user("bob", "bob@example.com")

        # The second user only exists on the other database
        alice = User.objects.using("other").get(username="alice")

        self.assertEqual(alice.username, "alice")
        self.assertEqual(alice._state.db, "other")

        with self.assertRaises(User.DoesNotExist):
            User.objects.using("default").get(username="alice")

        # The second user only exists on the default database
        bob = User.objects.using("default").get(username="bob")

        self.assertEqual(bob.username, "bob")
        self.assertEqual(bob._state.db, "default")

        with self.assertRaises(User.DoesNotExist):
            User.objects.using("other").get(username="bob")

        # That is... there is one user on each database
        self.assertEqual(User.objects.using("default").count(), 1)
        self.assertEqual(User.objects.using("other").count(), 1)