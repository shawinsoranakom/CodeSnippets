def _l10n_tr_nilvera_get_documents(self, invoice_channel="einvoice", document_category="Purchase", journal_type="purchase"):
        with _get_nilvera_client(self.env.company) as client:
            endpoint = f"/{invoice_channel}/{quote(document_category)}"
            start_date = self._get_nilvera_last_fetch_date(invoice_channel, journal_type)
            end_date = fields.Datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            page = 1

            # We filter documents by their CreatedDate on Nilvera, which represents when the document was created on
            # their platform. This ensures we always fetch the most recently uploaded documents, regardless of their
            # actual invoicing date (which might be much older).
            # The sorting allows us to resume from the last successfully fetched document in case an error interrupts
            # the batch fetching process.
            params = {
                'StatusCode': ['succeed'],
                'StartDate': start_date,
                'EndDate': end_date,
                'DateFilterType': 'CreatedDate',
                'SortColumn': 'CreationDateTime',
                'SortType': 'ASC',
            }
            response = client.request("GET", endpoint, params={**params, "Page": page})
            total_pages = response.get("TotalPages")
            if not total_pages:
                return

            moves = self.env['account.move']
            journal = self._l10n_tr_get_nilvera_invoice_journal(journal_type)
            date_param_key = f"l10n_tr_nilvera_{invoice_channel}_{journal_type}.last_fetched_date.{self.env.company.id}"
            while page <= total_pages:
                # Reuse first response, fetch subsequent pages.
                if page > 1:
                    response = client.request("GET", endpoint, params={**params, "Page": page})

                uuid_to_created_date = {
                    content.get('UUID'): content.get('CreatedDate')
                    for content in response.get('Content')
                }
                existing_document_uuids = {
                    rec['l10n_tr_nilvera_uuid'] for rec in self.env['account.move'].search_read(
                        [('l10n_tr_nilvera_uuid', 'in', list(uuid_to_created_date))],
                        ['l10n_tr_nilvera_uuid'],
                    )
                }
                for document_uuid, created_date in uuid_to_created_date.items():
                    # Skip invoices that have already been downloaded.
                    if document_uuid in existing_document_uuids:
                        continue
                    move = self._l10n_tr_nilvera_get_invoice_from_uuid(client, journal, document_uuid, document_category, invoice_channel)
                    self._l10n_tr_nilvera_add_pdf_to_invoice(client, move, document_uuid, document_category, invoice_channel)
                    moves |= move
                    # Update the last fetched date.
                    self.env['ir.config_parameter'].sudo().set_param(date_param_key, created_date)
                    self.env.cr.commit()
                page += 1
            journal._notify_einvoices_received(moves)