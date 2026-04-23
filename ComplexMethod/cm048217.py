def _send_submitted_expenses_mail(self):
        new_mails = []
        for company, expenses_submitted_per_company in self.grouped('company_id').items():
            parent_company_mails = company.parent_ids[::-1].mapped('email_formatted')
            mail_from = (
                    self.env.user.email
                    or company.email_formatted
                    or (parent_company_mails and parent_company_mails[0])
            )

            if not mail_from:  # We can't send a mail without sender
                _logger.warning(_("Failed to send mails for submitted expenses. No valid email was found for the company"))
                continue

            for manager, expenses_submitted in expenses_submitted_per_company.grouped('manager_id').items():
                if not manager:
                    continue
                manager_langs = tuple(lang for lang in manager.partner_id.mapped('lang') if lang)
                mail_lang = (manager_langs and manager_langs[0]) or self.env.lang or 'en_US'
                body = self.env['ir.qweb']._render(
                    template='hr_expense.hr_expense_template_submitted_expenses',
                    values={'manager_name': manager.name, 'url': '/odoo/expenses-to-process', 'company': company},
                    lang=mail_lang,
                )
                new_mails.append({
                    'author_id': self.env.user.partner_id.id,
                    'auto_delete': True,
                    'body_html': body,
                    'email_from': mail_from,
                    'email_to': manager.employee_id.work_email or manager.email,
                    'subject': _("New expenses waiting for your approval"),
                })
            if new_mails:
                self.env['mail.mail'].sudo().create(new_mails).send()