def _prepare_mail_values(self, res_ids):
        # When being in mass mailing mode, add 'mailing.trace' values directly in the o2m field of mail.mail.
        mail_values_all = super()._prepare_mail_values(res_ids)

        if not self._is_mass_mailing():
            return mail_values_all

        trace_values_all = self._prepare_mail_values_mailing_traces(mail_values_all)
        with file_open("mass_mailing/static/src/scss/mass_mailing_mail.scss", "r") as fd:
            styles = fd.read()
        for res_id, mail_values in mail_values_all.items():
            if mail_values.get('body_html'):
                body = self.env['ir.qweb']._render(
                    'mass_mailing.mass_mailing_mail_layout',
                    {'body': mail_values['body_html'], 'mailing_style': Markup(f'<style>{styles}</style>')},
                    minimal_qcontext=True,
                    raise_if_not_found=False
                )
                if body:
                    mail_values['body_html'] = body
            if mail_values.get('body'):
                mail_values['body'] = Markup(
                    '<div><span>{mailing_sent_message}</span></div>'
                    '<blockquote class="border-start" data-o-mail-quote="1" data-o-mail-quote-node="1">'
                    '{original_body}'
                    '</blockquote>'
                ).format(
                    mailing_sent_message=Markup(_(
                        'Received the mailing <b>{mailing_name}</b>',
                    )).format(
                        mailing_name=self.mass_mailing_name or self.mass_mailing_id.display_name
                    ),
                    original_body=mail_values['body'],
                )

            mail_values.update({
                'mailing_id': self.mass_mailing_id.id,
                'mailing_trace_ids': [(0, 0, trace_values_all[res_id])] if res_id in trace_values_all else False,
            })
        return mail_values_all