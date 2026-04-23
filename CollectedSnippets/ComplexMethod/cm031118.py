def run_test(self, test, create=None, *, compile_=None, unlink=None):
        """Test the finding of 'test' with the creation of modules listed in
        'create'.

        Any names listed in 'compile_' are byte-compiled. Modules
        listed in 'unlink' have their source files deleted.

        """
        if create is None:
            create = {test}
        if (compile_ or unlink) and sys.implementation.cache_tag is None:
            raise unittest.SkipTest('requires sys.implementation.cache_tag')
        with util.create_modules(*create) as mapping:
            if compile_:
                for name in compile_:
                    py_compile.compile(mapping[name])
            if unlink:
                for name in unlink:
                    os.unlink(mapping[name])
                    try:
                        make_legacy_pyc(mapping[name])
                    except OSError as error:
                        # Some tests do not set compile_=True so the source
                        # module will not get compiled and there will be no
                        # PEP 3147 pyc file to rename.
                        if error.errno != errno.ENOENT:
                            raise
            loader = self.import_(mapping['.root'], test)
            self.assertHasAttr(loader, 'exec_module')
            return loader