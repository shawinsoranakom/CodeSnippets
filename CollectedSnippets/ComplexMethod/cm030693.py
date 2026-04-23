def _make_pkg(self, source, depth, mod_base="runpy_test",
                     *, namespace=False, parent_namespaces=False):
        # Enforce a couple of internal sanity checks on test cases
        if (namespace or parent_namespaces) and not depth:
            raise RuntimeError("Can't mark top level module as a "
                               "namespace package")
        pkg_name = "__runpy_pkg__"
        test_fname = mod_base+os.extsep+"py"
        pkg_dir = sub_dir = os.path.realpath(tempfile.mkdtemp())
        if verbose > 1: print("  Package tree in:", sub_dir)
        sys.path.insert(0, pkg_dir)
        if verbose > 1: print("  Updated sys.path:", sys.path[0])
        if depth:
            namespace_flags = [parent_namespaces] * depth
            namespace_flags[-1] = namespace
            for namespace_flag in namespace_flags:
                sub_dir = os.path.join(sub_dir, pkg_name)
                pkg_fname = self._add_pkg_dir(sub_dir, namespace_flag)
                if verbose > 1: print("  Next level in:", sub_dir)
                if verbose > 1: print("  Created:", pkg_fname)
        mod_fname = os.path.join(sub_dir, test_fname)
        with open(mod_fname, "w") as mod_file:
            mod_file.write(source)
        if verbose > 1: print("  Created:", mod_fname)
        mod_name = (pkg_name+".")*depth + mod_base
        mod_spec = importlib.util.spec_from_file_location(mod_name,
                                                          mod_fname)
        return pkg_dir, mod_fname, mod_name, mod_spec