def _get_module_code(self, fullname):
    path = _get_module_path(self, fullname)
    import_error = None
    for suffix, isbytecode, ispackage in _zip_searchorder:
        fullpath = path + suffix
        _bootstrap._verbose_message('trying {}{}{}', self.archive, path_sep, fullpath, verbosity=2)
        try:
            toc_entry = self._get_files()[fullpath]
        except KeyError:
            pass
        else:
            modpath = toc_entry[0]
            data = _get_data(self.archive, toc_entry)
            code = None
            if isbytecode:
                try:
                    code = _unmarshal_code(self, modpath, fullpath, fullname, data)
                except ImportError as exc:
                    import_error = exc
            else:
                code = _compile_source(modpath, data, fullname)
            if code is None:
                # bad magic number or non-matching mtime
                # in byte code, try next
                continue
            modpath = toc_entry[0]
            return code, ispackage, modpath
    else:
        if import_error:
            msg = f"module load failed: {import_error}"
            raise ZipImportError(msg, name=fullname) from import_error
        else:
            raise ZipImportError(f"can't find module {fullname!r}", name=fullname)