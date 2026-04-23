def _create_attachments_from_inline_images(self, b64images):
        if not b64images:
            return []

        IrAttachment = self.env['ir.attachment']
        existing_attachments = dict(IrAttachment.search([
            ('res_model', '=', 'mailing.mailing'),
            ('res_id', '=', self.id),
        ]).mapped(lambda record: (record.checksum, record)))

        attachments, vals_for_attachs, checksums = [], [], []
        checksums_set, checksum_original_id, new_attachment_by_checksum = set(), {}, {}
        next_img_id = len(existing_attachments)
        for (b64image, original_id) in b64images:
            checksum = IrAttachment._compute_checksum(base64.b64decode(b64image))
            checksums.append(checksum)
            existing_attach = existing_attachments.get(checksum)
            # Existing_attach can be None, in which case it acts as placeholder
            # for attachment to be created.
            attachments.append(existing_attach)
            if original_id:
                checksum_original_id[checksum] = original_id
            if not existing_attach and not checksum in checksums_set:
                # We create only one attachment per checksum
                vals_for_attachs.append({
                    'datas': b64image,
                    'name': f"image_mailing_{self.id}_{next_img_id}",
                    'type': 'binary',
                    'res_id': self.id,
                    'res_model': 'mailing.mailing',
                    'checksum': checksum,
                })
                checksums_set.add(checksum)
                next_img_id += 1
        for vals in vals_for_attachs:
            if vals['checksum'] in checksum_original_id:
                vals['original_id'] = checksum_original_id[vals['checksum']]
            del vals['checksum']

        new_attachments = iter(IrAttachment.create(vals_for_attachs))
        checksum_iter = iter(checksums)
        # Replace None entries by newly created attachments.
        for i in range(len(attachments)):
            checksum = next(checksum_iter)
            if attachments[i]:
                continue
            if checksum in new_attachment_by_checksum:
                attachments[i] = new_attachment_by_checksum[checksum]
            else:
                attachments[i] = next(new_attachments)
                new_attachment_by_checksum[checksum] = attachments[i]

        urls = []
        for attachment in attachments:
            attachment.generate_access_token()
            urls.append('/web/image/%s?access_token=%s' % (attachment.id, attachment.access_token))

        return urls