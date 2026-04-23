def _get_stream_from(
        self, record, field_name='raw', filename=None, filename_field='name',
        mimetype=None, default_mimetype='application/octet-stream',
    ):
        """
        Create a :class:odoo.http.Stream: from a record's binary field.

        :param record: the record where to load the data from.
        :param str field_name: the binary field where to load the data
            from.
        :param Optional[str] filename: when the stream is downloaded by
            a browser, what filename it should have on disk. By default
            it is ``{model}-{id}-{field}.{extension}``, the extension is
            determined thanks to mimetype.
        :param Optional[str] filename_field: like ``filename`` but use
            one of the record's char field as filename.
        :param Optional[str] mimetype: the data mimetype to use instead
            of the stored one (attachment) or the one determined by
            magic.
        :param str default_mimetype: the mimetype to use when the
            mimetype couldn't be determined. By default it is
            ``application/octet-stream``.
        :rtype: odoo.http.Stream
        """
        with replace_exceptions(ValueError, by=UserError(f'Expected singleton: {record}')):  # pylint: disable=missing-gettext
            record.ensure_one()

        try:
            field_def = record._fields[field_name]
        except KeyError:
            raise UserError(f"Record has no field {field_name!r}.")  # pylint: disable=missing-gettext
        if field_def.type != 'binary':
            raise UserError(  # pylint: disable=missing-gettext
                f"Field {field_def!r} is type {field_def.type!r} but "
                f"it is only possible to stream Binary or Image fields."
            )

        stream = self._record_to_stream(record, field_name)

        if stream.type in ('data', 'path'):
            if mimetype:
                stream.mimetype = mimetype
            elif not stream.mimetype:
                if stream.type == 'data':
                    head = stream.data[:MIMETYPE_HEAD_SIZE]
                else:
                    with open(stream.path, 'rb') as file:
                        head = file.read(MIMETYPE_HEAD_SIZE)
                stream.mimetype = guess_mimetype(head, default=default_mimetype)

            if filename:
                stream.download_name = filename
            elif filename_field in record:
                stream.download_name = record[filename_field]
            if not stream.download_name:
                stream.download_name = f'{record._table}-{record.id}-{field_name}'

            stream.download_name = stream.download_name.replace('\n', '_').replace('\r', '_')
            if (not get_extension(stream.download_name)
                and stream.mimetype != 'application/octet-stream'):
                stream.download_name += guess_extension(stream.mimetype) or ''

        return stream