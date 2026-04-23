def __eq__(self, other):
        try:
            len_other = len(other)
        except TypeError:
            return NotImplemented

        self_name = ''
        if len(self) == 2:
            self_args, self_kwargs = self
        else:
            self_name, self_args, self_kwargs = self

        if (getattr(self, '_mock_parent', None) and getattr(other, '_mock_parent', None)
                and self._mock_parent != other._mock_parent):
            return False

        other_name = ''
        if len_other == 0:
            other_args, other_kwargs = (), {}
        elif len_other == 3:
            other_name, other_args, other_kwargs = other
        elif len_other == 1:
            value, = other
            if isinstance(value, tuple):
                other_args = value
                other_kwargs = {}
            elif isinstance(value, str):
                other_name = value
                other_args, other_kwargs = (), {}
            else:
                other_args = ()
                other_kwargs = value
        elif len_other == 2:
            # could be (name, args) or (name, kwargs) or (args, kwargs)
            first, second = other
            if isinstance(first, str):
                other_name = first
                if isinstance(second, tuple):
                    other_args, other_kwargs = second, {}
                else:
                    other_args, other_kwargs = (), second
            else:
                other_args, other_kwargs = first, second
        else:
            return False

        if self_name and other_name != self_name:
            return False

        # this order is important for ANY to work!
        return (other_args, other_kwargs) == (self_args, self_kwargs)