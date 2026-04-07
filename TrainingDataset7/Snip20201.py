def test_custom_manager_basic(self):
        """
        Test a custom Manager method.
        """
        self.assertQuerySetEqual(Person.objects.get_fun_people(), ["Bugs Bunny"], str)