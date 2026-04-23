def modify_image(self, attachment, res_model=None, res_id=None, name=None, data=None, original_id=None, mimetype=None, alt_data=None):
        """
        Creates a modified copy of an attachment and returns its image_src to be
        inserted into the DOM.
        """
        self._clean_context()
        attachment = request.env['ir.attachment'].browse(attachment.id)
        if not data and attachment.datas:
            data = attachment.datas

        fields = {
            'original_id': attachment.id,
            'datas': data,
            'type': 'binary',
            'res_model': res_model or 'ir.ui.view',
            'mimetype': mimetype or attachment.mimetype,
            'name': name or attachment.name,
            'res_id': 0,
        }
        if fields['res_model'] == 'ir.ui.view':
            fields['res_id'] = 0
        elif res_id:
            fields['res_id'] = res_id
        if fields['mimetype'] == 'image/webp':
            fields['name'] = re.sub(r'\.(jpe?g|png)$', '.webp', fields['name'], flags=re.I)

        existing_attachment = get_existing_attachment(request.env['ir.attachment'], fields)
        if existing_attachment and not existing_attachment.url:
            attachment = existing_attachment
        else:
            # Restricted editors can handle attachments related to records to
            # which they have access.
            # Would user be able to read fields of original record?
            if attachment.res_model and attachment.res_id:
                request.env[attachment.res_model].browse(attachment.res_id).check_access('read')

            # Would user be able to write fields of target record?
            # Rights check works with res_id=0 because browse(0) returns an
            # empty record set.
            request.env[fields['res_model']].browse(fields['res_id']).check_access('write')

            # Sudo because restricted editor will not be able to copy the record
            attachment = attachment.sudo().copy(fields).sudo(False)
            # Override mimetype with SUPERUSER if it was forced to plain text
            if attachment.mimetype == 'text/plain' != fields['mimetype']:
                attachment.with_user(SUPERUSER_ID).mimetype = fields['mimetype']

        if alt_data:
            for size, per_type in alt_data.items():
                reference_id = attachment.id
                if 'image/webp' in per_type:
                    resized = attachment.create_unique([{
                        'name': attachment.name,
                        'description': 'resize: %s' % size,
                        'datas': per_type['image/webp'],
                        'res_id': reference_id,
                        'res_model': 'ir.attachment',
                        'mimetype': 'image/webp',
                    }])
                    reference_id = resized[0]
                if 'image/jpeg' in per_type:
                    attachment.create_unique([{
                        'name': re.sub(r'\.webp$', '.jpg', attachment.name, flags=re.I),
                        'description': 'format: jpeg',
                        'datas': per_type['image/jpeg'],
                        'res_id': reference_id,
                        'res_model': 'ir.attachment',
                        'mimetype': 'image/jpeg',
                    }])

        if attachment.url:
            # Don't keep url if modifying static attachment because static images
            # are only served from disk and don't fallback to attachments.
            if re.match(r'^/\w+/static/', attachment.url):
                attachment.url = None
            # Uniquify url by adding a path segment with the id before the name.
            # This allows us to keep the unsplash url format so it still reacts
            # to the unsplash beacon.
            else:
                url_fragments = attachment.url.split('/')
                url_fragments.insert(-1, str(attachment.id))
                attachment.url = '/'.join(url_fragments)

        if attachment.public:
            return attachment.image_src

        attachment.generate_access_token()
        return '%s?access_token=%s' % (attachment.image_src, attachment.access_token)