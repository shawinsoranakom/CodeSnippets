def test_queryset_copied_to_default(self):
        """
        The methods of a custom QuerySet are properly copied onto the
        default Manager.
        """
        for manager_name in self.custom_manager_names:
            with self.subTest(manager_name=manager_name):
                manager = getattr(Person, manager_name)

                # Public methods are copied
                manager.public_method()
                # Private methods are not copied
                with self.assertRaises(AttributeError):
                    manager._private_method()