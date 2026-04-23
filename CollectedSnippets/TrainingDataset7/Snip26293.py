def test_abstract_manager(self):
        # Accessing the manager on an abstract model should
        # raise an attribute error with an appropriate message.
        # This error message isn't ideal, but if the model is abstract and
        # a lot of the class instantiation logic isn't invoked; if the
        # manager is implied, then we don't get a hook to install the
        # error-raising manager.
        msg = "type object 'AbstractBase3' has no attribute 'objects'"
        with self.assertRaisesMessage(AttributeError, msg):
            AbstractBase3.objects.all()