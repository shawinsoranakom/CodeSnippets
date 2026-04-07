def test_manager_attributes(self):
        """
        Custom manager method is only available on the manager and not on
        querysets.
        """
        Person.custom_queryset_custom_manager.manager_only()
        msg = "'CustomQuerySet' object has no attribute 'manager_only'"
        with self.assertRaisesMessage(AttributeError, msg):
            Person.custom_queryset_custom_manager.all().manager_only()