def _read_csv(self, options):
        """ Returns file length and a CSV-parsed list of all non-empty lines in the file.

        :raises csv.Error: if an error is detected during CSV parsing
        """
        csv_data = self.file or b''
        if not csv_data:
            return ()

        encoding = options.get('encoding')
        encoding_guessed = False
        if not encoding:
            encoding_guessed = True
            encoding = options['encoding'] = chardet.detect(csv_data)['encoding'].lower()
            # some versions of chardet (e.g. 2.3.0 but not 3.x) will return
            # utf-(16|32)(le|be), which for python means "ignore / don't strip
            # BOM". We don't want that, so rectify the encoding to non-marked
            # IFF the guessed encoding is LE/BE and csv_data starts with a BOM
            bom = BOM_MAP.get(encoding)
            if bom and csv_data.startswith(bom):
                encoding = options['encoding'] = encoding[:-2]

        try:
            csv_text = csv_data.decode(encoding)
        except UnicodeDecodeError as exc:
            if encoding_guessed:
                msg = _("There was an issue decoding the file using encoding “%s”.\nThis encoding was automatically detected.", encoding)
            else:
                msg = _("There was an issue decoding the file using encoding “%s”.\nThis encoding was manually selected.", encoding)
            raise ImportValidationError(msg) from exc

        separator = options.get('separator')
        if not separator:
            # default for unspecified separator so user gets a message about
            # having to specify it
            separator = ','
            for candidate in (',', ';', '\t', ' ', '|', unicodedata.lookup('unit separator')):
                # pass through the CSV and check if all rows are the same
                # length & at least 2-wide assume it's the correct one
                it = csv.reader(io.StringIO(csv_text), quotechar=options['quoting'], delimiter=candidate)
                w = None
                for row in it:
                    width = len(row)
                    if w is None:
                        w = width
                    if width == 1 or width != w:
                        break # next candidate
                else: # nobreak
                    separator = options['separator'] = candidate
                    break

        if not len(options['quoting']) == 1:
            raise ImportValidationError(_("Error while importing records: Text Delimiter should be a single character."))

        csv_iterator = csv.reader(
            io.StringIO(csv_text),
            quotechar=options['quoting'],
            delimiter=separator)

        content = [
            row for row in csv_iterator
            if any(x for x in row if x.strip())
        ]

        # return the file length as first value
        return len(content), content