def test_queryset_and_manager(self):
        """
        Queryset method doesn't override the custom manager method.
        """
        queryset = Person.custom_queryset_custom_manager.filter()
        self.assertQuerySetEqual(queryset, ["Bugs Bunny"], str)
        self.assertIs(queryset._filter_CustomManager, True)