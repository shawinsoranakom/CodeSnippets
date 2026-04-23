def test_unregister_unregistered_model(self):
        msg = "The model Person is not registered"
        with self.assertRaisesMessage(NotRegistered, msg):
            self.site.unregister(Person)