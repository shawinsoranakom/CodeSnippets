def _constraint_methods(self):
        """ Return a list of methods implementing Python constraints. """
        def is_constraint(func):
            return callable(func) and hasattr(func, '_constrains')

        def wrap(func, names):
            # wrap func into a proxy function with explicit '_constrains'
            @api.constrains(*names)
            def wrapper(self):
                return func(self)
            return wrapper

        cls = self.env.registry[self._name]
        methods = []
        for attr, func in getmembers(cls, is_constraint):
            if callable(func._constrains):
                func = wrap(func, func._constrains(self.sudo()))
            for name in func._constrains:
                field = cls._fields.get(name)
                if not field:
                    _logger.warning("method %s.%s: @constrains parameter %r is not a field name", cls._name, attr, name)
                elif not (field.store or field.inverse or field.inherited):
                    _logger.warning("method %s.%s: @constrains parameter %r is not writeable", cls._name, attr, name)
            methods.append(func)

        # optimization: memoize result on cls, it will not be recomputed
        cls._constraint_methods = methods
        return methods