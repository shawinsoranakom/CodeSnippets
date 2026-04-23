def check(count_val):
            reg.reset_mock()
            count.return_value = count_val
            Driver.ensure_registered()
            if count_val:
                self.assertFalse(reg.called)
            else:
                reg.assert_called_once_with()