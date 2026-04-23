def _overdue_invoices_get_page_view_values(self, overdue_invoices, **kwargs):
        values = {'page_name': 'overdue_invoices'}

        if len(overdue_invoices) == 0:
            return values

        first_invoice = overdue_invoices[0]
        partner = first_invoice.partner_id
        company = first_invoice.company_id
        currency = first_invoice.currency_id

        if any(invoice.partner_id != partner for invoice in overdue_invoices):
            raise ValidationError(_("Overdue invoices should share the same partner."))
        if any(invoice.company_id != company for invoice in overdue_invoices):
            raise ValidationError(_("Overdue invoices should share the same company."))
        if any(invoice.currency_id != currency for invoice in overdue_invoices):
            raise ValidationError(_("Overdue invoices should share the same currency."))

        total_amount = sum(overdue_invoices.mapped('amount_total'))
        amount_residual = sum(overdue_invoices.mapped('amount_residual'))
        batch_name = company.get_next_batch_payment_communication() if len(overdue_invoices) > 1 else first_invoice.name
        values.update({
            'payment': {
                'date': fields.Date.today(),
                'reference': batch_name,
                'amount': total_amount,
                'currency': currency,
            },
            'amount': total_amount,
        })

        common_view_values = self._get_common_page_view_values(
            invoices_data={
                'partner': partner,
                'company': company,
                'total_amount': total_amount,
                'currency': currency,
                'amount_residual': amount_residual,
                'payment_reference': batch_name,
                'landing_route': '/my/invoices/',
                'transaction_route': '/invoice/transaction/overdue',
            },
            **kwargs)
        values |= common_view_values
        return values