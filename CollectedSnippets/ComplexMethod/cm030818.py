def test_all(self):
        # List of denied modules and packages
        denylist = set([
            # Will raise a SyntaxError when compiling the exec statement
            '__future__',
        ])

        # In case _socket fails to build, make this test fail more gracefully
        # than an AttributeError somewhere deep in concurrent.futures, email
        # or unittest.
        import _socket  # noqa: F401

        ignored = []
        failed_imports = []
        lib_dir = os.path.dirname(os.path.dirname(__file__))
        for path, modname in self.walk_modules(lib_dir, ""):
            m = modname
            denied = False
            while m:
                if m in denylist:
                    denied = True
                    break
                m = m.rpartition('.')[0]
            if denied:
                continue
            if support.verbose:
                print(f"Check {modname}", flush=True)
            try:
                # This heuristic speeds up the process by removing, de facto,
                # most test modules (and avoiding the auto-executing ones).
                with open(path, "rb") as f:
                    if b"__all__" not in f.read():
                        raise NoAll(modname)
                self.check_all(modname)
            except NoAll:
                ignored.append(modname)
            except FailedImport:
                failed_imports.append(modname)

        if support.verbose:
            print('Following modules have no __all__ and have been ignored:',
                  ignored)
            print('Following modules failed to be imported:', failed_imports)