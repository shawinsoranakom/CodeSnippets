def test_explicit_abstract_manager(self):
        # Accessing the manager on an abstract model with an explicit
        # manager should raise an attribute error with an appropriate
        # message.
        msg = "Manager isn't available; AbstractBase1 is abstract"
        with self.assertRaisesMessage(AttributeError, msg):
            AbstractBase1.objects.all()