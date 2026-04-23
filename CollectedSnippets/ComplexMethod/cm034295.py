def __call__(*args, **kwargs):
        def _unpack_self(self, *args):
            return self, args

        self, args = _unpack_self(*args)

        # If enabled has been specified, then evaluate it at this point
        # and if the wrapper is not to be executed, then simply return
        # the bound function rather than a bound wrapper for the bound
        # function. When evaluating enabled, if it is callable we call
        # it, otherwise we evaluate it as a boolean.

        if self._self_enabled is not None:
            if callable(self._self_enabled):
                if not self._self_enabled():
                    return self.__wrapped__(*args, **kwargs)
            elif not self._self_enabled:
                return self.__wrapped__(*args, **kwargs)

        # This can occur where initial function wrapper was applied to
        # a function that was already bound to an instance. In that case
        # we want to extract the instance from the function and use it.

        if self._self_binding in ('function', 'instancemethod', 'classmethod', 'callable'):
            if self._self_instance is None:
                instance = getattr(self.__wrapped__, '__self__', None)
                if instance is not None:
                    return self._self_wrapper(self.__wrapped__, instance,
                            args, kwargs)

        # This is generally invoked when the wrapped function is being
        # called as a normal function and is not bound to a class as an
        # instance method. This is also invoked in the case where the
        # wrapped function was a method, but this wrapper was in turn
        # wrapped using the staticmethod decorator.

        return self._self_wrapper(self.__wrapped__, self._self_instance,
                args, kwargs)