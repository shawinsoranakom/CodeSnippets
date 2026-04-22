def __init__(self, obj):
            self._obj = obj

            # Override all the Wrapped object's magic functions
            for name in Wrapper._get_magic_functions(obj.__class__):
                setattr(
                    self.__class__,
                    name,
                    property(self._make_magic_function_proxy(name)),
                )