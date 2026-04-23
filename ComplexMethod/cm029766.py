def _from_module(self, module, object):
        """
        Return true if the given object is defined in the given
        module.
        """
        if module is None:
            return True
        elif inspect.getmodule(object) is not None:
            return module is inspect.getmodule(object)
        elif inspect.isfunction(object):
            return module.__dict__ is object.__globals__
        elif (inspect.ismethoddescriptor(object) or
              inspect.ismethodwrapper(object)):
            if hasattr(object, '__objclass__'):
                obj_mod = object.__objclass__.__module__
            elif hasattr(object, '__module__'):
                obj_mod = object.__module__
            else:
                return True # [XX] no easy way to tell otherwise
            return module.__name__ == obj_mod
        elif inspect.isclass(object):
            return module.__name__ == object.__module__
        elif hasattr(object, '__module__'):
            return module.__name__ == object.__module__
        elif isinstance(object, property):
            return True # [XX] no way not be sure.
        else:
            raise ValueError("object must be a class or function")