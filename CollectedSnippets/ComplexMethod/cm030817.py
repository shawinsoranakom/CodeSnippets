def walk_modules(self, basedir, modpath):
        for fn in sorted(os.listdir(basedir)):
            path = os.path.join(basedir, fn)
            if os.path.isdir(path):
                if fn in SKIP_MODULES:
                    continue
                pkg_init = os.path.join(path, '__init__.py')
                if os.path.exists(pkg_init):
                    yield pkg_init, modpath + fn
                    for p, m in self.walk_modules(path, modpath + fn + "."):
                        yield p, m
                continue

            if fn == '__init__.py':
                continue
            if not fn.endswith('.py'):
                continue
            modname = fn.removesuffix('.py')
            if modname in SKIP_MODULES:
                continue
            yield path, modpath + modname