def ismethod(oclass, obj, name):
            classdict = oclass.__dict__
            if isinstance(obj, MethodType):
                # could be a classmethod
                if (not isinstance(classdict[name], ClassMethodType) or
                    obj.__self__ is not oclass):
                    return False
            elif not isinstance(obj, FunctionType):
                return False

            objname = obj.__name__
            if objname.startswith("__") and not objname.endswith("__"):
                if stripped_typename := oclass.__name__.lstrip('_'):
                    objname = f"_{stripped_typename}{objname}"
            return objname == name