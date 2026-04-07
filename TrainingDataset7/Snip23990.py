def test_registered(self, reg, count):
        """
        Prototypes are registered only if the driver count is zero.
        """

        def check(count_val):
            reg.reset_mock()
            count.return_value = count_val
            Driver.ensure_registered()
            if count_val:
                self.assertFalse(reg.called)
            else:
                reg.assert_called_once_with()

        check(0)
        check(120)