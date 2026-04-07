def test_get_model_admin_unregister_model(self):
        msg = "The model Person is not registered."
        with self.assertRaisesMessage(NotRegistered, msg):
            self.site.get_model_admin(Person)