def insert_attachment(self, model_sudo, id_record, files):
        if not model_sudo.env.su:
            raise ValueError("model_sudo should get passed with sudo")
        model_name = model_sudo.model
        orphan_attachment_ids = []
        record = model_sudo.env[model_name].browse(id_record)
        authorized_fields = model_sudo.with_user(SUPERUSER_ID)._get_form_writable_fields()
        for file in files:
            custom_field = file.field_name not in authorized_fields
            attachment_value = {
                'name': file.filename,
                'datas': base64.encodebytes(file.read()),
                'res_model': model_name,
                'res_id': record.id,
            }
            attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)
            if attachment_id and not custom_field:
                record_sudo = record.sudo()
                value = [(4, attachment_id.id)]
                if record_sudo._fields[file.field_name].type == 'many2one':
                    value = attachment_id.id
                record_sudo[file.field_name] = value
            else:
                orphan_attachment_ids.append(attachment_id.id)

        if model_name != 'mail.mail' and hasattr(record, '_message_log') and orphan_attachment_ids:
            # If some attachments didn't match a field on the model,
            # we create a mail.message to link them to the record
            record._message_log(
                attachment_ids=[(6, 0, orphan_attachment_ids)],
                body=Markup(_('<p>Attached files: </p>')),
                message_type='comment',
            )
        elif model_name == 'mail.mail' and orphan_attachment_ids:
            # If the model is mail.mail then we have no other choice but to
            # attach the custom binary field files on the attachment_ids field.
            for attachment_id_id in orphan_attachment_ids:
                record.attachment_ids = [(4, attachment_id_id)]