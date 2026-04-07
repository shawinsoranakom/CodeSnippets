def test_manager_honors_queryset_only(self):
        for manager_name in self.custom_manager_names:
            with self.subTest(manager_name=manager_name):
                manager = getattr(Person, manager_name)
                # Methods with queryset_only=False are copied even if they are
                # private.
                manager._optin_private_method()
                # Methods with queryset_only=True aren't copied even if they
                # are public.
                msg = (
                    "%r object has no attribute 'optout_public_method'"
                    % manager.__class__.__name__
                )
                with self.assertRaisesMessage(AttributeError, msg):
                    manager.optout_public_method()