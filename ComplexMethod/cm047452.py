def iter_module_files(self, *globs, modules=None):
        """ Yields the paths of all the module files matching the provided globs
        (AND-ed)
        """
        if modules is None:
            module_roots = [m.path for m in Manifest.all_addon_manifests()]
        else:
            module_roots = [m.path for name in modules if (m := Manifest.for_addon(name))]
        for modroot in module_roots:
            for root, _, fnames in os.walk(modroot):
                fnames = [opj(root, n) for n in fnames]
                for glob in globs:
                    fnames = fnmatch.filter(fnames, glob)
                yield from fnames