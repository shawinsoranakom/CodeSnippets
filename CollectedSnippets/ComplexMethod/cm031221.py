def wm_attributes(self, *args, return_python_dict=False, **kwargs):
        """Return or sets platform specific attributes.

        When called with a single argument return_python_dict=True,
        return a dict of the platform specific attributes and their values.
        When called without arguments or with a single argument
        return_python_dict=False, return a tuple containing intermixed
        attribute names with the minus prefix and their values.

        When called with a single string value, return the value for the
        specific option.  When called with keyword arguments, set the
        corresponding attributes.
        """
        if not kwargs:
            if not args:
                res = self.tk.call('wm', 'attributes', self._w)
                if return_python_dict:
                    return _splitdict(self.tk, res)
                else:
                    return self.tk.splitlist(res)
            if len(args) == 1 and args[0] is not None:
                option = args[0]
                if option[0] == '-':
                    # TODO: deprecate
                    option = option[1:]
                return self.tk.call('wm', 'attributes', self._w, '-' + option)
            # TODO: deprecate
            return self.tk.call('wm', 'attributes', self._w, *args)
        elif args:
            raise TypeError('wm_attribute() options have been specified as '
                            'positional and keyword arguments')
        else:
            self.tk.call('wm', 'attributes', self._w, *self._options(kwargs))