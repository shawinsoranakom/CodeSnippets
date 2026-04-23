def find(self, obj, name=None, module=None, globs=None, extraglobs=None):
        """
        Return a list of the DocTests that are defined by the given
        object's docstring, or by any of its contained objects'
        docstrings.

        The optional parameter `module` is the module that contains
        the given object.  If the module is not specified or is None, then
        the test finder will attempt to automatically determine the
        correct module.  The object's module is used:

            - As a default namespace, if `globs` is not specified.
            - To prevent the DocTestFinder from extracting DocTests
              from objects that are imported from other modules.
            - To find the name of the file containing the object.
            - To help find the line number of the object within its
              file.

        Contained objects whose module does not match `module` are ignored.

        If `module` is False, no attempt to find the module will be made.
        This is obscure, of use mostly in tests:  if `module` is False, or
        is None but cannot be found automatically, then all objects are
        considered to belong to the (non-existent) module, so all contained
        objects will (recursively) be searched for doctests.

        The globals for each DocTest is formed by combining `globs`
        and `extraglobs` (bindings in `extraglobs` override bindings
        in `globs`).  A new copy of the globals dictionary is created
        for each DocTest.  If `globs` is not specified, then it
        defaults to the module's `__dict__`, if specified, or {}
        otherwise.  If `extraglobs` is not specified, then it defaults
        to {}.

        """
        # If name was not specified, then extract it from the object.
        if name is None:
            name = getattr(obj, '__name__', None)
            if name is None:
                raise ValueError("DocTestFinder.find: name must be given "
                        "when obj.__name__ doesn't exist: %r" %
                                 (type(obj),))

        # Find the module that contains the given object (if obj is
        # a module, then module=obj.).  Note: this may fail, in which
        # case module will be None.
        if module is False:
            module = None
        elif module is None:
            module = inspect.getmodule(obj)

        # Read the module's source code.  This is used by
        # DocTestFinder._find_lineno to find the line number for a
        # given object's docstring.
        try:
            file = inspect.getsourcefile(obj)
        except TypeError:
            source_lines = None
        else:
            if not file:
                # Check to see if it's one of our special internal "files"
                # (see __patched_linecache_getlines).
                file = inspect.getfile(obj)
                if not file[0]+file[-2:] == '<]>': file = None
            if file is None:
                source_lines = None
            else:
                if module is not None:
                    # Supply the module globals in case the module was
                    # originally loaded via a PEP 302 loader and
                    # file is not a valid filesystem path
                    source_lines = linecache.getlines(file, module.__dict__)
                else:
                    # No access to a loader, so assume it's a normal
                    # filesystem path
                    source_lines = linecache.getlines(file)
                if not source_lines:
                    source_lines = None

        # Initialize globals, and merge in extraglobs.
        if globs is None:
            if module is None:
                globs = {}
            else:
                globs = module.__dict__.copy()
        else:
            globs = globs.copy()
        if extraglobs is not None:
            globs.update(extraglobs)
        if '__name__' not in globs:
            globs['__name__'] = '__main__'  # provide a default module name

        # Recursively explore `obj`, extracting DocTests.
        tests = []
        self._find(tests, obj, name, module, source_lines, globs, {})
        # Sort the tests by alpha order of names, for consistency in
        # verbose-mode output.  This was a feature of doctest in Pythons
        # <= 2.3 that got lost by accident in 2.4.  It was repaired in
        # 2.4.4 and 2.5.
        tests.sort()
        return tests