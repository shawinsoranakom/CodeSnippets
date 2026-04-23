def _l10n_pl_edi_download_bills_from_ksef(self):

        def handle_download_bills_from_ksef_error(error):
            if not (delay := error.get('retry_after')):
                raise UserError(error.get('message'))

            cron = self.env.ref('l10n_pl_edi.cron_l10n_pl_edi_ksef_download_bills')
            cron._trigger(at=fields.Datetime.now() + relativedelta(seconds=delay))
            return True

        service = KsefApiService(self.env.company)

        last_processed_move = self.search([
            ('l10n_pl_edi_number', '!=', False),
            ('move_type', '=', 'in_invoice'),
            *self._check_company_domain(self.env.company)
        ], order='invoice_date DESC', limit=1)

        if last_processed_move:
            date_from = fields.Datetime.to_datetime(last_processed_move.invoice_date)
        else:
            date_from = fields.Datetime.now() - relativedelta(months=1)

        query = {
            'subjectType': 'Subject2',
            'dateRange': {
                'from': date_from.isoformat(),
                'to': fields.Datetime.now().isoformat(),
                'dateType': 'Invoicing',
            },
        }

        # Rate Limiting of get_invoice_by_ksef_number
        #
        #     req/s  |  req/m  |  req/h
        #   -----------------------------
        #       8    |    16   |    64
        #
        # Page size shouldn't be more than 64.

        page_offset = 0
        page_size = 64

        has_more = True

        invoice_numbers = []
        blocking_error = False

        while has_more:
            response = service.query_invoice_metadata(query, page_size, page_offset)
            if response.get('error'):
                blocking_error = handle_download_bills_from_ksef_error(response['error'])
                break
            invoice_numbers.extend(invoice['ksefNumber'] for invoice in response['invoices'])
            has_more = response['hasMore']
            page_offset += 1

        already_processed = set(self.env['account.move'].search([
            ('l10n_pl_edi_number', 'in', invoice_numbers)
        ]).mapped('l10n_pl_edi_number'))

        to_process = [invoice_nr for invoice_nr in invoice_numbers if invoice_nr not in already_processed]

        bills_vals_list = []

        for invoice_nr in to_process:
            response = service.get_invoice_by_ksef_number(invoice_nr)
            if response.get('error'):
                blocking_error = handle_download_bills_from_ksef_error(response['error'])
                break
            bill_data = self.l10n_pl_edi_get_ksef_bill_vals_from_xml(response['xml_content'])
            bill_data['l10n_pl_edi_number'] = invoice_nr
            bills_vals_list.append(bill_data)

        self.create(bills_vals_list)

        return blocking_error