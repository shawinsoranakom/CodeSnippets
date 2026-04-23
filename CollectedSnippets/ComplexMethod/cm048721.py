def _send_mails(self, moves_data):
        subtype = self.env.ref('mail.mt_comment')

        self._generate_dynamic_reports(moves_data)

        for move, move_data in [
            (move, move_data)
            for move, move_data in moves_data.items()
            if move.partner_id.email or move_data.get('mail_partner_ids')
        ]:
            mail_template = move_data['mail_template']
            mail_lang = move_data['mail_lang']
            mail_params = self._get_mail_params(move, move_data)
            if not mail_params:
                continue

            if move_data.get('proforma_pdf_attachment'):
                attachment = move_data['proforma_pdf_attachment']
                mail_params['attachments'].append((attachment.name, attachment.raw))

            # synchronize author / email_from, as account.move.send wizard computes
            # a bit too much stuff
            author_id = mail_params.pop('author_id', False)
            email_from = self._get_mail_default_field_value_from_template(mail_template, mail_lang, move, 'email_from')
            if email_from or not author_id:
                author_id, email_from = move._message_compute_author(email_from=email_from)
            model_description = move.with_context(lang=mail_lang).type_name

            self._send_mail(
                move,
                mail_template,
                author_id=author_id,
                subtype_id=subtype.id,
                model_description=model_description,
                notify_author_mention=True,
                email_from=email_from,
                **mail_params,
            )