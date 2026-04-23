def _resolve_filename(cls, fullname, alias=None, ispkg=False):
        if not fullname or not getattr(sys, '_stdlib_dir', None):
            return None, None
        try:
            sep = cls._SEP
        except AttributeError:
            sep = cls._SEP = '\\' if sys.platform == 'win32' else '/'

        if fullname != alias:
            if fullname.startswith('<'):
                fullname = fullname[1:]
                if not ispkg:
                    fullname = f'{fullname}.__init__'
            else:
                ispkg = False
        relfile = fullname.replace('.', sep)
        if ispkg:
            pkgdir = f'{sys._stdlib_dir}{sep}{relfile}'
            filename = f'{pkgdir}{sep}__init__.py'
        else:
            pkgdir = None
            filename = f'{sys._stdlib_dir}{sep}{relfile}.py'
        return filename, pkgdir