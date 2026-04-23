def _get_image_stream_from(
        self, record, field_name='raw', filename=None, filename_field='name',
        mimetype=None, default_mimetype='image/png', placeholder=None,
        width=0, height=0, crop=False, quality=0,
    ):
        """
        Create a :class:odoo.http.Stream: from a record's binary field,
        equivalent of :meth:`~get_stream_from` but for images.

        In case the record does not exist or is not accessible, the
        alternative ``placeholder`` path is used instead. If not set,
        a path is determined via
        :meth:`~odoo.models.BaseModel._get_placeholder_filename` which
        ultimately fallbacks on ``web/static/img/placeholder.png``.

        In case the arguments ``width``, ``height``, ``crop`` or
        ``quality`` are given, the image will be post-processed and the
        ETags (the unique cache http header) will be updated
        accordingly. See also :func:`odoo.tools.image.image_process`.

        :param record: the record where to load the data from.
        :param str field_name: the binary field where to load the data
            from.
        :param Optional[str] filename: when the stream is downloaded by
            a browser, what filename it should have on disk. By default
            it is ``{table}-{id}-{field}.{extension}``, the extension is
            determined thanks to mimetype.
        :param Optional[str] filename_field: like ``filename`` but use
            one of the record's char field as filename.
        :param Optional[str] mimetype: the data mimetype to use instead
            of the stored one (attachment) or the one determined by
            magic.
        :param str default_mimetype: the mimetype to use when the
            mimetype couldn't be determined. By default it is
            ``image/png``.
        :param Optional[pathlike] placeholder: in case the image is not
            found or unaccessible, the path of an image to use instead.
            By default the record ``_get_placeholder_filename`` on the
            requested field or ``web/static/img/placeholder.png``.
        :param int width: if not zero, the width of the resized image.
        :param int height: if not zero, the height of the resized image.
        :param bool crop: if true, crop the image instead of rezising
            it.
        :param int quality: if not zero, the quality of the resized
            image.

        """
        stream = None
        try:
            stream = self._get_stream_from(
                record, field_name, filename, filename_field, mimetype,
                default_mimetype
            )
        except UserError:
            if request.params.get('download'):
                raise

        if not stream or stream.size == 0:
            if not placeholder:
                placeholder = record._get_placeholder_filename(field_name)
            stream = self._get_placeholder_stream(placeholder)

        if stream.type == 'url':
            return stream  # Rezising an external URL is not supported
        if not stream.mimetype.startswith('image/'):
            stream.mimetype = 'application/octet-stream'

        if (width, height) == (0, 0):
            width, height = image_guess_size_from_field_name(field_name)

        if isinstance(stream.etag, str):
            stream.etag += f'-{width}x{height}-crop={crop}-quality={quality}'
        if isinstance(stream.last_modified, (int, float)):
            stream.last_modified = datetime.fromtimestamp(stream.last_modified, tz=None)
        modified = werkzeug.http.is_resource_modified(
            request.httprequest.environ,
            etag=stream.etag if isinstance(stream.etag, str) else None,
            last_modified=stream.last_modified
        )

        if modified and (width or height or crop):
            if stream.type == 'path':
                with open(stream.path, 'rb') as file:
                    stream.type = 'data'
                    stream.path = None
                    stream.data = file.read()
            stream.data = image_process(
                stream.data,
                size=(width, height),
                crop=crop,
                quality=quality,
            )
            stream.size = len(stream.data)

        return stream