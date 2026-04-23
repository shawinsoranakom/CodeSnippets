def __mod__(self, rhs):
                if isinstance(rhs, dict) and number:
                    number_value = self._get_number_value(rhs)
                else:
                    number_value = rhs
                translated = self._translate(number_value)
                try:
                    translated %= rhs
                except TypeError:
                    # String doesn't contain a placeholder for the number.
                    pass
                return translated