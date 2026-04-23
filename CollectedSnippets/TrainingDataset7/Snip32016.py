def test_max_recursion_error(self):
        """
        Overriding a method on a super class and then calling that method on
        the super class should not trigger infinite recursion. See #17011.
        """
        super().test_max_recursion_error()