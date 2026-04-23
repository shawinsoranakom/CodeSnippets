def _check_make_stub_pages(self):
        """ The stub is the summary of paid invoices. It may spill on several pages, in which case only the check on
            first page is valid. This function returns a list of stub lines per page.
        """
        self.ensure_one()

        def prepare_vals(invoice, partials=None, current_amount=0):
            invoice_name = invoice.name or '/'
            number = ' - '.join([invoice_name, invoice.ref] if invoice.ref else [invoice_name])

            if invoice.is_outbound() or invoice.move_type == 'in_receipt':
                invoice_sign = 1
                partial_field = 'debit_amount_currency'
            else:
                invoice_sign = -1
                partial_field = 'credit_amount_currency'

            amount_residual = invoice.amount_residual - current_amount
            if invoice.currency_id.is_zero(amount_residual):
                amount_residual_str = '-'
            else:
                amount_residual_str = formatLang(self.env, invoice_sign * amount_residual, currency_obj=invoice.currency_id)
            amount_paid = current_amount if current_amount else sum(partials.mapped(partial_field))

            return {
                'due_date': format_date(self.env, invoice.invoice_date_due),
                'number': number,
                'amount_total': formatLang(self.env, invoice_sign * invoice.amount_total, currency_obj=invoice.currency_id),
                'amount_residual': amount_residual_str,
                'amount_paid': formatLang(self.env, invoice_sign * amount_paid, currency_obj=self.currency_id),
                'currency': invoice.currency_id,
            }

        if self.move_id:
            # Decode the reconciliation to keep only invoices.
            term_lines = self.move_id.line_ids.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))
            invoices = (term_lines.matched_debit_ids.debit_move_id.move_id + term_lines.matched_credit_ids.credit_move_id.move_id)\
                .filtered(lambda x: x.is_outbound(include_receipts=True))

            # Group partials by invoices.
            invoice_map = {invoice: self.env['account.partial.reconcile'] for invoice in invoices}
            for partial in term_lines.matched_debit_ids:
                invoice = partial.debit_move_id.move_id
                if invoice in invoice_map:
                    invoice_map[invoice] |= partial
            for partial in term_lines.matched_credit_ids:
                invoice = partial.credit_move_id.move_id
                if invoice in invoice_map:
                    invoice_map[invoice] |= partial
        else:
            invoices = self.invoice_ids.filtered(lambda x: x.is_outbound(include_receipts=True))
            remaining = self.amount

        stub_lines = []
        type_groups = {
            ('in_invoice', 'in_receipt'): _("Bills"),
            ('out_refund',): _("Refunds"),
        }
        invoices_grouped = invoices.grouped(lambda i: next(group for group in type_groups if i.move_type in group))
        for type_group, invoices in invoices_grouped.items():
            invoices = iter(invoices.sorted(lambda x: x.invoice_date_due or x.date))
            if len(invoices_grouped) > 1:
                stub_lines += [{'header': True, 'name': type_groups[type_group]}]
            if self.move_id:
                stub_lines += [
                    prepare_vals(invoice, partials=invoice_map[invoice])
                    for invoice in invoices
                ]
            else:
                while remaining and (invoice := next(invoices, None)):
                    current_amount = min(remaining, invoice.currency_id._convert(
                        from_amount=invoice.amount_residual,
                        to_currency=self.currency_id,
                    ))
                    stub_lines += [prepare_vals(invoice, current_amount=current_amount)]
                    remaining -= current_amount

        # Crop the stub lines or split them on multiple pages
        if not self.company_id.account_check_printing_multi_stub:
            # If we need to crop the stub, leave place for an ellipsis line
            num_stub_lines = len(stub_lines) > INV_LINES_PER_STUB and INV_LINES_PER_STUB - 1 or INV_LINES_PER_STUB
            stub_pages = [stub_lines[:num_stub_lines]]
        else:
            stub_pages = []
            i = 0
            while i < len(stub_lines):
                # Make sure we don't start the credit section at the end of a page
                if len(stub_lines) >= i + INV_LINES_PER_STUB and stub_lines[i + INV_LINES_PER_STUB - 1].get('header'):
                    num_stub_lines = INV_LINES_PER_STUB - 1 or INV_LINES_PER_STUB
                else:
                    num_stub_lines = INV_LINES_PER_STUB
                stub_pages.append(stub_lines[i:i + num_stub_lines])
                i += num_stub_lines

        return stub_pages