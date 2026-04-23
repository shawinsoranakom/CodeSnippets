def __call__(*args, **kwargs):
        def _unpack_self(self, *args):
            return self, args

        self, args = _unpack_self(*args)

        # If enabled has been specified, then evaluate it at this point and if
        # the wrapper is not to be executed, then simply return the bound
        # function rather than a bound wrapper for the bound function. When
        # evaluating enabled, if it is callable we call it, otherwise we
        # evaluate it as a boolean.

        if self._self_enabled is not None:
            if callable(self._self_enabled):
                if not self._self_enabled():
                    return self.__wrapped__(*args, **kwargs)
            elif not self._self_enabled:
                return self.__wrapped__(*args, **kwargs)

        # We need to do things different depending on whether we are likely
        # wrapping an instance method vs a static method or class method.

        if self._self_binding == 'function':
            if self._self_instance is None and args:
                instance, newargs = args[0], args[1:]
                if isinstance(instance, self._self_owner):
                    wrapped = PartialCallableObjectProxy(self.__wrapped__, instance)
                    return self._self_wrapper(wrapped, instance, newargs, kwargs)

            return self._self_wrapper(self.__wrapped__, self._self_instance,
                    args, kwargs)

        elif self._self_binding == 'callable':
            if self._self_instance is None:
                # This situation can occur where someone is calling the
                # instancemethod via the class type and passing the instance as
                # the first argument. We need to shift the args before making
                # the call to the wrapper and effectively bind the instance to
                # the wrapped function using a partial so the wrapper doesn't
                # see anything as being different.

                if not args:
                    raise TypeError('missing 1 required positional argument')

                instance, args = args[0], args[1:]
                wrapped = PartialCallableObjectProxy(self.__wrapped__, instance)
                return self._self_wrapper(wrapped, instance, args, kwargs)

            return self._self_wrapper(self.__wrapped__, self._self_instance,
                    args, kwargs)

        else:
            # As in this case we would be dealing with a classmethod or
            # staticmethod, then _self_instance will only tell us whether
            # when calling the classmethod or staticmethod they did it via an
            # instance of the class it is bound to and not the case where
            # done by the class type itself. We thus ignore _self_instance
            # and use the __self__ attribute of the bound function instead.
            # For a classmethod, this means instance will be the class type
            # and for a staticmethod it will be None. This is probably the
            # more useful thing we can pass through even though we loose
            # knowledge of whether they were called on the instance vs the
            # class type, as it reflects what they have available in the
            # decoratored function.

            instance = getattr(self.__wrapped__, '__self__', None)

            return self._self_wrapper(self.__wrapped__, instance, args,
                    kwargs)