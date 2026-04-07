def test_manager_use_queryset_methods(self):
        """
        Custom manager will use the queryset methods
        """
        for manager_name in self.custom_manager_names:
            with self.subTest(manager_name=manager_name):
                manager = getattr(Person, manager_name)
                queryset = manager.filter()
                self.assertQuerySetEqual(queryset, ["Bugs Bunny"], str)
                self.assertIs(queryset._filter_CustomQuerySet, True)

                # Specialized querysets inherit from our custom queryset.
                queryset = manager.values_list("first_name", flat=True).filter()
                self.assertEqual(list(queryset), ["Bugs"])
                self.assertIs(queryset._filter_CustomQuerySet, True)

                self.assertIsInstance(queryset.values(), CustomQuerySet)
                self.assertIsInstance(queryset.values().values(), CustomQuerySet)
                self.assertIsInstance(queryset.values_list().values(), CustomQuerySet)