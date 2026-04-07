def __call__(self, *args, **kwargs):
                value = super().__call__(*args, **kwargs)
                self.call_return_value_list.append(value)
                return value