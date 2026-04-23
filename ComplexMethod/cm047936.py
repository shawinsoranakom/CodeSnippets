def parse_preview(self, options, count=10):
        """ Generates a preview of the uploaded files, and performs
            fields-matching between the import's file data and the model's
            columns.

            If the headers are not requested (not options.has_headers),
            returned ``matches`` and ``headers`` are both ``False``.

            :param int count: number of preview lines to generate
            :param options: format-specific options.
                            CSV: {quoting, separator, headers}
            :type options: {str, str, str, bool}
            :returns: ``{fields, matches, headers, preview} | {error, preview}``
            :rtype: {dict(str: dict(...)), dict(int, list(str)), list(str), list(list(str))} | {str, str}
        """
        self.ensure_one()
        fields_tree = self.get_fields_tree(self.res_model)
        try:
            file_length, data_rows = self._read_file(options)
            if file_length <= 0:
                raise ImportValidationError(_("Import file has no content or is corrupt"))

            preview = data_rows[:count]

            # Get file headers
            if options.get('has_headers') and preview:
                # We need the header types before matching columns to fields
                headers = preview.pop(0)
                header_types = self._extract_headers_types(headers, preview, options)
            else:
                header_types, headers = {}, []

            # Get matches: the ones already selected by the user or propose a new matching.
            matches = {}
            # If user checked to the advanced mode, we re-parse the file but we keep the mapping "as is".
            # No need to make another mapping proposal
            if options.get('keep_matches') and options.get('fields'):
                for index, match in enumerate(options.get('fields', [])):
                    if match:
                        matches[index] = match.split('/')
            elif options.get('has_headers'):
                matches = self._get_mapping_suggestions(headers, header_types, fields_tree)
                # remove header_name for matches keys as tuples are no supported in json.
                # and remove distance from suggestion (keep only the field path) as not used at client side.
                matches = {
                    header_key[0]: suggestion['field_path']
                    for header_key, suggestion in matches.items()
                    if suggestion
                }

            # compute if we should activate advanced mode or not:
            # if was already activated of if file contains "relational fields".
            if options.get('keep_matches'):
                advanced_mode = options.get('advanced')
            else:
                # Check is label contain relational field
                has_relational_header = any(len(models.fix_import_export_id_paths(col)) > 1 for col in headers)
                # Check is matches fields have relational field
                has_relational_match = any(len(match) > 1 for field, match in matches.items() if match)
                advanced_mode = has_relational_header or has_relational_match

            # Take first non null values for each column to show preview to users.
            # Initially first non null value is displayed to the user.
            # On hover preview consists in 5 values.
            column_example = []
            for column_index, _unused in enumerate(preview[0]):
                vals = []
                for record in preview:
                    val = record[column_index]
                    if val and isinstance(val, str):
                        vals.append("%s%s" % (record[column_index][:50], "..." if len(record[column_index]) > 50 else ""))
                    elif isinstance(val, datetime.datetime):
                        vals.append(val.strftime(options.get('datetime_format') or DEFAULT_SERVER_DATETIME_FORMAT))
                    elif isinstance(val, datetime.date):
                        vals.append(val.strftime(options.get('date_format') or DEFAULT_SERVER_DATE_FORMAT))
                    if len(vals) == 5:
                        break
                column_example.append(
                    vals or
                    [""]  # blank value if no example have been found at all for the current column
                )

            # Batch management
            batch = False
            batch_cutoff = options.get('limit')
            if batch_cutoff:
                if count > batch_cutoff:
                    batch = len(preview) > batch_cutoff
                else:
                    batch = bool(next(
                        itertools.islice(data_rows, batch_cutoff - count, None),
                        None
                    ))

            return {
                'fields': fields_tree,
                'matches': matches or False,
                'headers': headers or False,
                'header_types': list(header_types.values()) or False,
                'preview': column_example,
                'options': options,
                'advanced_mode': advanced_mode,
                'debug': self.env.user.has_group('base.group_no_one'),
                'batch': batch,
                'num_rows': len(data_rows),
            }
        except Exception as error:
            # Due to lazy generators, UnicodeDecodeError (for
            # instance) may only be raised when serializing the
            # preview to a list in the return.
            _logger.debug("Error during parsing preview", exc_info=True)
            preview = None
            if self.file_type == 'text/csv' and self.file:
                preview = self.file[:ERROR_PREVIEW_BYTES].decode('iso-8859-1')
            return {
                'error': str(error),
                # iso-8859-1 ensures decoding will always succeed,
                # even if it yields non-printable characters. This is
                # in case of UnicodeDecodeError (or csv.Error
                # compounded with UnicodeDecodeError)
                'preview': preview,
            }