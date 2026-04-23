def action_create_vendor_bill(self):
        """ This function is called by the "try our sample" button of Vendor Bills,
        visible on dashboard if no bill has been created yet.
        """
        context = dict(self.env.context)
        purchase_journal = self.browse(context.get('default_journal_id')) or self.search([('type', '=', 'purchase')], limit=1)
        partner = self.env.ref('base.res_partner_2', raise_if_not_found=False)
        if not purchase_journal:
            raise UserError(self._build_no_journal_error_msg(self.env.company.display_name, ['purchase']))
        if not partner:
            raise UserError(_('You may only use samples in demo mode, try uploading one of your invoices instead.'))
        context['default_move_type'] = 'in_invoice'
        invoice_date = fields.Date.today() - timedelta(days=12)
        partner = self.env.ref('base.res_partner_2', raise_if_not_found=False)
        company = purchase_journal.company_id
        default_expense_account = company.expense_account_id
        ref = 'DE%s' % invoice_date.strftime('%Y%m')
        bill = self.env['account.move'].with_context(default_extract_state='done').create({
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'ref': ref,
            'invoice_date': invoice_date,
            'invoice_date_due': invoice_date + timedelta(days=30),
            'journal_id': purchase_journal.id,
            'invoice_line_ids': [
                Command.create({
                    'name': "[FURN_8999] Three-Seat Sofa",
                    'account_id': purchase_journal.default_account_id.id or default_expense_account.id,
                    'quantity': 5,
                    'price_unit': 1500,
                }),
                Command.create({
                    'name': "[FURN_8220] Four Person Desk",
                    'account_id': purchase_journal.default_account_id.id or default_expense_account.id,
                    'quantity': 5,
                    'price_unit': 2350,
                })
            ],
        })
        # In case of test environment, don't create the pdf
        if tools.config['test_enable']:
            bill.message_post()
        else:
            addr = [x for x in [
                company.street,
                company.street2,
                ' '.join([x for x in [company.state_id.name, company.zip] if x]),
                company.country_id.name,
            ] if x]

            html = self.env['ir.qweb']._render('account.bill_preview', {
                'company_name': company.name,
                'company_street_address': addr,
                'invoice_name': 'Invoice ' + ref,
                'invoice_ref': ref,
                'invoice_date': invoice_date,
                'invoice_due_date': invoice_date + timedelta(days=30),
            })
            bodies = self.env['ir.actions.report']._prepare_html(html)[0]
            content = self.env['ir.actions.report']._run_wkhtmltopdf(bodies)
            attachment = self.env['ir.attachment'].create({
                'type': 'binary',
                'name': 'INV-%s-0001.pdf' % invoice_date.strftime('%Y-%m'),
                'res_model': 'mail.compose.message',
                'datas': base64.encodebytes(content),
            })
            bill.message_post(attachment_ids=attachment.ids)
        return {
            'name': _('Bills'),
            'res_id': bill.id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'views': [[False, "form"]],
            'type': 'ir.actions.act_window',
            'context': context,
        }