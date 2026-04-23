def filter(self, name=None, filter_func=None, **flags):
        """
        Register a callable as a template filter. Example:

        @register.filter
        def lower(value):
            return value.lower()
        """
        if name is None and filter_func is None:
            # @register.filter()
            def dec(func):
                return self.filter_function(func, **flags)

            return dec
        elif name is not None and filter_func is None:
            if callable(name):
                # @register.filter
                return self.filter_function(name, **flags)
            else:
                # @register.filter('somename') or
                # @register.filter(name='somename')
                def dec(func):
                    return self.filter(name, func, **flags)

                return dec
        elif name is not None and filter_func is not None:
            # register.filter('somename', somefunc)
            self.filters[name] = filter_func
            for attr in ("expects_localtime", "is_safe", "needs_autoescape"):
                if attr in flags:
                    value = flags[attr]
                    # set the flag on the filter for FilterExpression.resolve
                    setattr(filter_func, attr, value)
                    # set the flag on the innermost decorated function
                    # for decorators that need it, e.g. stringfilter
                    setattr(unwrap(filter_func), attr, value)
            filter_func._filter_name = name
            return filter_func
        else:
            raise ValueError(
                "Unsupported arguments to Library.filter: (%r, %r)"
                % (name, filter_func),
            )