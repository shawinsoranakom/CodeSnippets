def discover(self, start_dir, pattern='test*.py', top_level_dir=None):
        """Find and return all test modules from the specified start
        directory, recursing into subdirectories to find them and return all
        tests found within them. Only test files that match the pattern will
        be loaded. (Using shell style pattern matching.)

        All test modules must be importable from the top level of the project.
        If the start directory is not the top level directory then the top
        level directory must be specified separately.

        If a test package name (directory with '__init__.py') matches the
        pattern then the package will be checked for a 'load_tests' function. If
        this exists then it will be called with (loader, tests, pattern) unless
        the package has already had load_tests called from the same discovery
        invocation, in which case the package module object is not scanned for
        tests - this ensures that when a package uses discover to further
        discover child tests that infinite recursion does not happen.

        If load_tests exists then discovery does *not* recurse into the package,
        load_tests is responsible for loading all tests in the package.

        The pattern is deliberately not stored as a loader attribute so that
        packages can continue discovery themselves. top_level_dir is stored so
        load_tests does not need to pass this argument in to loader.discover().

        Paths are sorted before being imported to ensure reproducible execution
        order even on filesystems with non-alphabetical ordering like ext3/4.
        """
        original_top_level_dir = self._top_level_dir
        set_implicit_top = False
        if top_level_dir is None and self._top_level_dir is not None:
            # make top_level_dir optional if called from load_tests in a package
            top_level_dir = self._top_level_dir
        elif top_level_dir is None:
            set_implicit_top = True
            top_level_dir = start_dir

        top_level_dir = os.path.abspath(top_level_dir)

        if not top_level_dir in sys.path:
            # all test modules must be importable from the top level directory
            # should we *unconditionally* put the start directory in first
            # in sys.path to minimise likelihood of conflicts between installed
            # modules and development versions?
            sys.path.insert(0, top_level_dir)
        self._top_level_dir = top_level_dir

        is_not_importable = False
        is_namespace = False
        tests = []
        if os.path.isdir(os.path.abspath(start_dir)):
            start_dir = os.path.abspath(start_dir)
            if start_dir != top_level_dir:
                is_not_importable = not os.path.isfile(os.path.join(start_dir, '__init__.py'))
        else:
            # support for discovery from dotted module names
            try:
                __import__(start_dir)
            except ImportError:
                is_not_importable = True
            else:
                the_module = sys.modules[start_dir]
                if not hasattr(the_module, "__file__") or the_module.__file__ is None:
                    # look for namespace packages
                    try:
                        spec = the_module.__spec__
                    except AttributeError:
                        spec = None

                    if spec and spec.submodule_search_locations is not None:
                        is_namespace = True

                        for path in the_module.__path__:
                            if (not set_implicit_top and
                                not path.startswith(top_level_dir)):
                                continue
                            self._top_level_dir = \
                                (path.split(the_module.__name__
                                        .replace(".", os.path.sep))[0])
                            tests.extend(self._find_tests(path, pattern, namespace=True))
                    elif the_module.__name__ in sys.builtin_module_names:
                        # builtin module
                        raise TypeError('Can not use builtin modules '
                                        'as dotted module names') from None
                    else:
                        raise TypeError(
                            f"don't know how to discover from {the_module!r}"
                            ) from None

                else:
                    top_part = start_dir.split('.')[0]
                    start_dir = os.path.abspath(os.path.dirname((the_module.__file__)))

                if set_implicit_top:
                    if not is_namespace:
                        if sys.modules[top_part].__file__ is None:
                            self._top_level_dir = os.path.dirname(the_module.__file__)
                            if self._top_level_dir not in sys.path:
                                sys.path.insert(0, self._top_level_dir)
                        else:
                            self._top_level_dir = \
                                self._get_directory_containing_module(top_part)
                    sys.path.remove(top_level_dir)

        if is_not_importable:
            raise ImportError('Start directory is not importable: %r' % start_dir)

        if not is_namespace:
            tests = list(self._find_tests(start_dir, pattern))

        self._top_level_dir = original_top_level_dir
        return self.suiteClass(tests)