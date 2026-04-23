def __init__(self, wrapped, wrapper, enabled=None):
        # What it is we are wrapping here could be anything. We need to
        # try and detect specific cases though. In particular, we need
        # to detect when we are given something that is a method of a
        # class. Further, we need to know when it is likely an instance
        # method, as opposed to a class or static method. This can
        # become problematic though as there isn't strictly a fool proof
        # method of knowing.
        #
        # The situations we could encounter when wrapping a method are:
        #
        # 1. The wrapper is being applied as part of a decorator which
        # is a part of the class definition. In this case what we are
        # given is the raw unbound function, classmethod or staticmethod
        # wrapper objects.
        #
        # The problem here is that we will not know we are being applied
        # in the context of the class being set up. This becomes
        # important later for the case of an instance method, because in
        # that case we just see it as a raw function and can't
        # distinguish it from wrapping a normal function outside of
        # a class context.
        #
        # 2. The wrapper is being applied when performing monkey
        # patching of the class type afterwards and the method to be
        # wrapped was retrieved direct from the __dict__ of the class
        # type. This is effectively the same as (1) above.
        #
        # 3. The wrapper is being applied when performing monkey
        # patching of the class type afterwards and the method to be
        # wrapped was retrieved from the class type. In this case
        # binding will have been performed where the instance against
        # which the method is bound will be None at that point.
        #
        # This case is a problem because we can no longer tell if the
        # method was a static method, plus if using Python3, we cannot
        # tell if it was an instance method as the concept of an
        # unnbound method no longer exists.
        #
        # 4. The wrapper is being applied when performing monkey
        # patching of an instance of a class. In this case binding will
        # have been perfomed where the instance was not None.
        #
        # This case is a problem because we can no longer tell if the
        # method was a static method.
        #
        # Overall, the best we can do is look at the original type of the
        # object which was wrapped prior to any binding being done and
        # see if it is an instance of classmethod or staticmethod. In
        # the case where other decorators are between us and them, if
        # they do not propagate the __class__  attribute so that the
        # isinstance() checks works, then likely this will do the wrong
        # thing where classmethod and staticmethod are used.
        #
        # Since it is likely to be very rare that anyone even puts
        # decorators around classmethod and staticmethod, likelihood of
        # that being an issue is very small, so we accept it and suggest
        # that those other decorators be fixed. It is also only an issue
        # if a decorator wants to actually do things with the arguments.
        #
        # As to not being able to identify static methods properly, we
        # just hope that that isn't something people are going to want
        # to wrap, or if they do suggest they do it the correct way by
        # ensuring that it is decorated in the class definition itself,
        # or patch it in the __dict__ of the class type.
        #
        # So to get the best outcome we can, whenever we aren't sure what
        # it is, we label it as a 'callable'. If it was already bound and
        # that is rebound later, we assume that it will be an instance
        # method and try and cope with the possibility that the 'self'
        # argument it being passed as an explicit argument and shuffle
        # the arguments around to extract 'self' for use as the instance.

        binding = None

        if isinstance(wrapped, _FunctionWrapperBase):
            binding = wrapped._self_binding

        if not binding:
            if inspect.isbuiltin(wrapped):
                binding = 'builtin'

            elif inspect.isfunction(wrapped):
                binding = 'function'

            elif inspect.isclass(wrapped):
                binding = 'class'

            elif isinstance(wrapped, classmethod):
                binding = 'classmethod'

            elif isinstance(wrapped, staticmethod):
                binding = 'staticmethod'

            elif hasattr(wrapped, '__self__'):
                if inspect.isclass(wrapped.__self__):
                    binding = 'classmethod'
                elif inspect.ismethod(wrapped):
                    binding = 'instancemethod'
                else:
                    binding = 'callable'

            else:
                binding = 'callable'

        super(FunctionWrapper, self).__init__(wrapped, None, wrapper,
                enabled, binding)