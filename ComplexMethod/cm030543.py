def tearDown(self):
        sys.path[:] = self.syspath
        for modulename in self.modules_to_cleanup:
            if modulename in sys.modules:
                del sys.modules[modulename]
        if self.root: # Only clean if the test was actually run
            cleanout(self.root)

        # delete all modules concerning the tested hierarchy
        if self.pkgname:
            modules = [name for name in sys.modules
                       if self.pkgname in name.split('.')]
            for name in modules:
                del sys.modules[name]