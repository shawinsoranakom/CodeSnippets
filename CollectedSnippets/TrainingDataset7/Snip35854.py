def test_pickling(self):
        msg = "Cannot pickle ResolverMatch."
        with self.assertRaisesMessage(pickle.PicklingError, msg):
            pickle.dumps(resolve("/users/"))