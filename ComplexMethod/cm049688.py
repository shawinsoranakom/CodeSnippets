def _attachment_create(self, name='', data=False, url=False, res_id=False, res_model='ir.ui.view'):
        """Create and return a new attachment."""
        IrAttachment = request.env['ir.attachment']

        if name.lower().endswith('.bmp'):
            # Avoid mismatch between content type and mimetype, see commit msg
            name = name[:-4]

        if not name and url:
            name = url.split("/").pop()

        if res_model != 'ir.ui.view' and res_id:
            res_id = int(res_id)
        else:
            res_id = False

        attachment_data = {
            'name': name,
            'public': res_model == 'ir.ui.view',
            'res_id': res_id,
            'res_model': res_model,
        }

        if data:
            attachment_data['raw'] = data
            if url:
                attachment_data['url'] = url
        elif url:
            attachment_data.update({
                'type': 'url',
                'url': url,
            })
            # The code issues a HEAD request to retrieve headers from the URL.
            # This approach is beneficial when the URL doesn't conclude with an
            # image extension. By verifying the MIME type, the code ensures that
            # only supported image types are incorporated into the data.
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                mime_type = response.headers.get('content-type')
                if mime_type in SUPPORTED_IMAGE_MIMETYPES:
                    attachment_data['mimetype'] = mime_type
        else:
            raise UserError(_("You need to specify either data or url to create an attachment."))

        # Despite the user having no right to create an attachment, he can still
        # create an image attachment through some flows
        if (
            not request.env.is_admin()
            and IrAttachment._can_bypass_rights_on_media_dialog(**attachment_data)
        ):
            attachment = IrAttachment.sudo().create(attachment_data)
            # When portal users upload an attachment with the wysiwyg widget,
            # the access token is needed to use the image in the editor. If
            # the attachment is not public, the user won't be able to generate
            # the token, so we need to generate it using sudo
            if not attachment_data['public']:
                attachment.sudo().generate_access_token()
        else:
            attachment = get_existing_attachment(IrAttachment, attachment_data) \
                or IrAttachment.create(attachment_data)

        return attachment