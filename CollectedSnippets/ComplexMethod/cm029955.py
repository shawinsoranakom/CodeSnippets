def _is_stdlib_module(self, object, basedir=None):
        basedir = self.STDLIB_DIR if basedir is None else basedir

        try:
            file = inspect.getabsfile(object)
        except TypeError:
            file = '(built-in)'

        if sysconfig.is_python_build():
            srcdir = sysconfig.get_config_var('srcdir')
            if srcdir:
                basedir = os.path.join(srcdir, 'Lib')

        basedir = os.path.normcase(basedir)
        return (isinstance(object, type(os)) and
                (object.__name__ in ('errno', 'exceptions', 'gc',
                                     'marshal', 'posix', 'signal', 'sys',
                                     '_thread', 'zipimport')
                or (file.startswith(basedir) and
                 not file.startswith(os.path.join(basedir, 'site-packages')))))