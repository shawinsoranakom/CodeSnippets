def test_email_in_username(self):
        call_command(
            "createsuperuser",
            interactive=False,
            username="joe+admin@somewhere.org",
            email="joe@somewhere.org",
            verbosity=0,
        )
        u = User._default_manager.get(username="joe+admin@somewhere.org")
        self.assertEqual(u.email, "joe@somewhere.org")
        self.assertFalse(u.has_usable_password())