def test_custom_abstract_manager(self):
        # Accessing the manager on an abstract model with a custom
        # manager should raise an attribute error with an appropriate
        # message.
        msg = "Manager isn't available; AbstractBase2 is abstract"
        with self.assertRaisesMessage(AttributeError, msg):
            AbstractBase2.restricted.all()