def _read_file(self, options):
        """ Dispatch to specific method to read file content, according to its mimetype or file type

        :param dict options: reading options (quoting, separator, ...)
        """
        self.ensure_one()

        # guess mimetype from file content
        mimetype = guess_mimetype(self.file or b'')
        extensions_to_try = [
            (MIMETYPE_TO_READER.get(mimetype), f"guessed using mimetype {mimetype!r}"),
            (MIMETYPE_TO_READER.get(self.file_type), f"decided from user-provided mimetype {self.file_type!r}"),
        ]
        # fallback on file extensions as mime types can be unreliable (e.g.
        # software setting incorrect mime types, or non-installed software
        # leading to browser not sending mime types)
        if self.file_name:
            _stem, ext = os.path.splitext(self.file_name)
            extensions_to_try.append((ext.removeprefix('.'), f"decided from file extension {ext!r}"))

        e = None
        requires = None
        tried_extensions = set()
        for file_extension, guess_message in extensions_to_try:
            if not file_extension or file_extension in tried_extensions:
                continue
            tried_extensions.add(file_extension)
            try:
                handler = getattr(self, '_read_' + file_extension, None)
                if callable(handler):
                    return handler(options)
            except ImportError as exc:
                # exc.name_from attribute is present as of python 3.12
                requires = str(getattr(exc, 'name_from', None) or exc.name)
                if file_extension == 'xlsx':
                    # if xlrd 2.x then xlrd.xlsx is not available
                    requires = 'openpyxl or xlrd >= 1.0.0 < 2.0'
            except (ImportValidationError, ValueError):
                raise
            except Exception as exc:  # noqa: BLE001
                e = read_file_failed(exc, f"Unable to read file {self.file_name or '<unknown>'!r} as {file_extension!r} ({guess_message}).")

        if e is not None:
            raise e

        if requires:
            raise UserError(_("Unable to load \"{extension}\" file: requires Python module \"{modname}\"").format(extension=file_extension, modname=requires))
        raise UserError(_("Unsupported file format \"{}\", import only supports CSV, ODS, XLS and XLSX").format(self.file_type))