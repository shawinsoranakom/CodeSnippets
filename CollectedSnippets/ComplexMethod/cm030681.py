def checkModule(self, moduleName, module=None, ignore=()):
        ''' succeed iff pyclbr.readmodule_ex(modulename) corresponds
            to the actual module object, module.  Any identifiers in
            ignore are ignored.   If no module is provided, the appropriate
            module is loaded with __import__.'''

        ignore = set(ignore) | set(['object'])

        if module is None:
            # Import it.
            # ('<silly>' is to work around an API silliness in __import__)
            module = __import__(moduleName, globals(), {}, ['<silly>'])

        dict = pyclbr.readmodule_ex(moduleName)

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

        # Make sure the toplevel functions and classes are the same.
        for name, value in dict.items():
            if name in ignore:
                continue
            self.assertHasAttr(module, name)
            py_item = getattr(module, name)
            if isinstance(value, pyclbr.Function):
                self.assertIsInstance(py_item, (FunctionType, BuiltinFunctionType))
                if py_item.__module__ != moduleName:
                    continue   # skip functions that came from somewhere else
                self.assertEqual(py_item.__module__, value.module)
            else:
                self.assertIsInstance(py_item, type)
                if py_item.__module__ != moduleName:
                    continue   # skip classes that came from somewhere else

                real_bases = [base.__name__ for base in py_item.__bases__]
                pyclbr_bases = [ getattr(base, 'name', base)
                                 for base in value.super ]

                try:
                    self.assertListEq(real_bases, pyclbr_bases, ignore)
                except:
                    print("class=%s" % py_item, file=sys.stderr)
                    raise

                actualMethods = []
                for m in py_item.__dict__.keys():
                    if m == "__annotate__":
                        continue
                    if ismethod(py_item, getattr(py_item, m), m):
                        actualMethods.append(m)

                if stripped_typename := name.lstrip('_'):
                    foundMethods = []
                    for m in value.methods.keys():
                        if m.startswith('__') and not m.endswith('__'):
                            foundMethods.append(f"_{stripped_typename}{m}")
                        else:
                            foundMethods.append(m)
                else:
                    foundMethods = list(value.methods.keys())

                try:
                    self.assertListEq(foundMethods, actualMethods, ignore)
                    self.assertEqual(py_item.__module__, value.module)

                    self.assertEqualsOrIgnored(py_item.__name__, value.name,
                                               ignore)
                    # can't check file or lineno
                except:
                    print("class=%s" % py_item, file=sys.stderr)
                    raise

        # Now check for missing stuff.
        def defined_in(item, module):
            if isinstance(item, type):
                return item.__module__ == module.__name__
            if isinstance(item, FunctionType):
                return item.__globals__ is module.__dict__
            return False
        for name in dir(module):
            item = getattr(module, name)
            if isinstance(item,  (type, FunctionType)):
                if defined_in(item, module):
                    self.assertHaskey(dict, name, ignore)