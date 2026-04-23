def _convert_import_data(
        self,
        fields: Sequence[str | bool],
        options,
    ) -> tuple[
        list[list[str]],  # data
        list[str],        # fields, without the bool items
    ]:
        """ Extracts the input BaseModel and fields list (with
            ``False``-y placeholders for fields to *not* import) into a
            format Model.import_data can use: a fields list without holes
            and the precisely matching data matrix

            :returns: (data, fields)
            :raises ValueError: in case the import data could not be converted
        """
        # Get indices for non-empty fields
        indices = [index for index, field in enumerate(fields) if field]
        if not indices:
            raise ImportValidationError(_("You must configure at least one field to import"))
        # If only one index, itemgetter will return an atom rather
        # than a 1-tuple
        if len(indices) == 1:
            mapper = lambda row: [row[indices[0]]]
        else:
            mapper = operator.itemgetter(*indices)
        # Get only list of actually imported fields
        import_fields = [f for f in fields if f]

        _file_length, rows_to_import = self._read_file(options)
        if len(rows_to_import[0]) != len(fields):
            raise ImportValidationError(
                _(
                    "Error while importing records: all rows should be of the same size, but the title row has %(title_row_entries)d entries while the first row has %(first_row_entries)d. You may need to change the separator character.",
                    title_row_entries=len(fields),
                    first_row_entries=len(rows_to_import[0]),
                ),
            )

        if options.get('has_headers'):
            rows_to_import = rows_to_import[1:]
        data = [
            list(row) for row in map(mapper, rows_to_import)
            # don't try inserting completely empty rows (e.g. from
            # filtering out o2m fields)
            if any(row)
        ]

        # slicing needs to happen after filtering out empty rows as the
        # data offsets from load are post-filtering
        return data[options.get('skip'):], import_fields