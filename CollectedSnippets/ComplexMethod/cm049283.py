def _get_src_urls(self, record, field_name, options):
        """Considering the rendering options, returns the src and data-zoom-image urls.

        :return: src, src_zoom urls
        :rtype: tuple
        """
        max_size = None
        if options.get('resize'):
            max_size = options.get('resize')
        else:
            max_width, max_height = options.get('max_width', 0), options.get('max_height', 0)
            if max_width or max_height:
                max_size = '%sx%s' % (max_width, max_height)

        sha = hashlib.sha512(str(getattr(record, 'write_date', fields.Datetime.now())).encode('utf-8')).hexdigest()[:7]
        max_size = '' if max_size is None else '/%s' % max_size

        if options.get('filename-field') and options['filename-field'] in record and record[options['filename-field']]:
            filename = record[options['filename-field']]
        elif options.get('filename'):
            filename = options['filename']
        else:
            filename = record.display_name
        filename = (filename or 'name').replace('/', '-').replace('\\', '-').replace('..', '--')

        src = '/web/image/%s/%s/%s%s/%s?unique=%s' % (record._name, record.id, options.get('preview_image', field_name), max_size, url_quote(filename), sha)

        src_zoom = None
        if options.get('zoom') and getattr(record, options['zoom'], None):
            src_zoom = '/web/image/%s/%s/%s%s/%s?unique=%s' % (record._name, record.id, options['zoom'], max_size, url_quote(filename), sha)
        elif options.get('zoom'):
            src_zoom = options['zoom']

        return src, src_zoom