def format(self, *args, **kwargs):
                number_value = (
                    self._get_number_value(kwargs) if kwargs and number else args[0]
                )
                return self._translate(number_value).format(*args, **kwargs)