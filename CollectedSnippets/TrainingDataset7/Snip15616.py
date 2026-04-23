def test_prevent_double_registration(self):
        self.site.register(Person)
        msg = "The model Person is already registered in app 'admin_registration'."
        with self.assertRaisesMessage(AlreadyRegistered, msg):
            self.site.register(Person)