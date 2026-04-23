def theme_upload_font(self, name, data):
        """
        Uploads font binary data and returns metadata about accessing individual fonts.
        :param name: name of the uploaded file
        :param data: binary content of the uploaded file
        :return: list of dict describing each contained font with:
            - name
            - mimetype
            - attachment id
            - attachment URL
        """
        def check_content(filename, data):
            """ Returns True only if data matches the font extension. """
            # Do not pollute general guess_mimetype with this.
            ext = filename.rsplit('.')[-1].lower()
            if ext == 'otf':
                return data.startswith(b'OTTO')
            elif ext == 'woff':
                return data.startswith(b'wOFF')
            elif ext == 'woff2':
                return data.startswith(b'wOF2')
            elif ext == 'ttf':
                # Based on https://docs.fileformat.com/font/ttf/#true-type-file-format-specifications
                TOC_OFFSET = 12
                TOC_ENTRY_LENGTH = 16
                table_size = int.from_bytes(data[4:6], 'big') * TOC_ENTRY_LENGTH
                if TOC_OFFSET + table_size > len(data):
                    return False
                mandatory_tags = {b'cmap', b'glyf', b'head', b'hhea', b'hmtx', b'loca', b'maxp', b'name', b'post'}
                for offset in range(TOC_OFFSET, TOC_OFFSET + table_size, TOC_ENTRY_LENGTH):
                    tag = data[offset:offset + 4]
                    mandatory_tags.discard(tag)
                return not mandatory_tags
            return False

        def create_attachment(font, data):
            """ Creates font attachments right away to avoid keeping
            several extracted contents in memory. """
            ext = font['name'].rsplit('.')[-1].lower()
            font['mimetype'] = f'font/{ext}'
            attachment = request.env['ir.attachment'].create({
                'name': font['name'],
                'mimetype': font['mimetype'],
                'raw': data,
                'public': True,
            })
            font['id'] = attachment.id
            font['url'] = f"/web/content/{attachment.id}/{font['name']}"
            return font

        result = []
        binary_data = base64.b64decode(data, validate=True)
        readable_data = BytesIO(binary_data)
        if zipfile.is_zipfile(readable_data):
            with zipfile.ZipFile(readable_data, "r") as zip_file:
                for entry in zip_file.infolist():
                    if entry.file_size > MAX_FONT_FILE_SIZE:
                        raise UserError(_("File '%s' exceeds maximum allowed file size", entry.filename))
                    if entry.filename.rsplit('.', 1)[-1].lower() not in SUPPORTED_FONT_EXTENSIONS \
                            or entry.filename.startswith('__MACOSX') \
                            or '/.' in entry.filename:
                        continue
                    data = zip_file.read(entry)
                    if not check_content(entry.filename, data):
                        continue
                    result.append(create_attachment({
                        'name': f'{name}-{entry.filename.replace("/", "-")}',
                    }, data))
        elif name.rsplit('.', 1)[-1].lower() in SUPPORTED_FONT_EXTENSIONS and check_content(name, binary_data):
            result.append(create_attachment({
                'name': name,
            }, binary_data))
        if not result:
            raise UserError(_("File '%s' is not recognized as a font", name))
        return result