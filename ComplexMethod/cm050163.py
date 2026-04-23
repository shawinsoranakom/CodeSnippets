def _l10n_tr_nilvera_get_submitted_document_status(self):
        for company, invoices in self.grouped("company_id").items():
            with _get_nilvera_client(company) as client:
                for invoice in invoices:
                    invoice_channel = invoice.partner_id.l10n_tr_nilvera_customer_status
                    document_category = invoice._l10n_tr_get_document_category(invoice_channel)
                    if not document_category or not invoice_channel:
                        continue

                    response = client.request(
                        "GET",
                        f"/{invoice_channel}/{quote(document_category)}/{invoice.l10n_tr_nilvera_uuid}/Status",
                    )

                    nilvera_status = response.get('InvoiceStatus', {}).get('Code') or response.get('StatusCode')
                    if nilvera_status in dict(invoice._fields['l10n_tr_nilvera_send_status'].selection):
                        invoice.l10n_tr_nilvera_send_status = nilvera_status
                        if nilvera_status == 'error':
                            invoice.message_post(
                                body=Markup(
                                    "%s<br/>%s - %s<br/>"
                                ) % (
                                    _("The invoice couldn't be sent to the recipient."),
                                    response.get('InvoiceStatus', {}).get('Description') or response.get('StatusDetail'),
                                    response.get('InvoiceStatus', {}).get('DetailDescription') or response.get('ReportStatus'),
                                )
                            )
                    else:
                        invoice.message_post(body=_("The invoice status couldn't be retrieved from Nilvera."))