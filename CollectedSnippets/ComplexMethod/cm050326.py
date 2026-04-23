def _l10n_it_edi_import_invoice(self, invoice, data, is_new):
        """ Decode a FatturaPA attachment into an Odoo move.

        :param data:   the dictionary with the content to be imported
                       keys: 'name', 'raw', 'xml_tree', 'import_file_type'
        :param is_new: whether the move is newly created or to be updated
        :returns:      the imported move
        """
        with self._get_edi_creation() as self:
            buyer_seller_info = self._l10n_it_buyer_seller_info()

            tree = data['xml_tree']
            # Identify the first invoice if there are several in the file.
            tree = tree.find('.//FatturaElettronicaBody')
            company = self.company_id

            # There are 2 cases:
            # - cron:
            #     * Move direction (incoming / outgoing) flexible (no 'default_move_type')
            #     * I.e. used for import from tax agency
            # - "Upload" button (invoices / bills view)
            #     * Fixed move direction; the button sets the 'default_move_type'
            default_move_type = self.env.context.get('default_move_type')
            if default_move_type is None:
                incoming_possibilities = [True, False]
            elif default_move_type in invoice.get_purchase_types(include_receipts=True):
                incoming_possibilities = [True]
            elif default_move_type in invoice.get_sale_types(include_receipts=True):
                incoming_possibilities = [False]
            else:
                _logger.warning("Cannot handle default_move_type '%s'.", default_move_type)
                return

            for incoming in incoming_possibilities:
                company_role, partner_role = ('buyer', 'seller') if incoming else ('seller', 'buyer')
                company_info = buyer_seller_info[company_role]
                vat = get_text(tree, company_info['vat_xpath'])
                if vat and vat .casefold() in (company.vat or '').casefold():
                    break
                codice_fiscale = get_text(tree, company_info['codice_fiscale_xpath'])
                if codice_fiscale and codice_fiscale.casefold() in (company.l10n_it_codice_fiscale or '').casefold():
                    break
            else:
                invoice.message_post(body=_("Your company's VAT number and Fiscal Code haven't been found in the buyer and/or seller sections inside the document."))
                return

            # For unsupported document types, just assume in_invoice, and log that the type is unsupported
            document_type = get_text(tree, '//DatiGeneraliDocumento/TipoDocumento')
            if l10n_it_document_type := self.env['l10n_it.document.type'].search([('code', '=', document_type)]):
                self.l10n_it_document_type = l10n_it_document_type

            move_type = self._l10n_it_edi_document_type_mapping().get(document_type, {}).get('import_type')
            if not move_type:
                move_type = "in_invoice"
                _logger.info('Document type not managed: %s. Invoice type is set by default.', document_type)
            if not incoming and move_type.startswith('in_'):
                move_type = 'out' + move_type[2:]

            self.move_type = move_type

            # Set the move journal to the preferred/default purchase journal set from the italian EDI settings
            if self.move_type in self.get_purchase_types(include_receipts=True) and self.company_id.l10n_it_edi_purchase_journal_id:
                self.journal_id = self.company_id.l10n_it_edi_purchase_journal_id

            if self.name and self.name != '/':
                # the journal might've changed, so we need to recompute the name in case it was set (first entry in journal)
                self.name = False
                self._compute_name()

            # Collect extra info from the XML that may be used by submodules to further put information on the invoice lines
            extra_info, message_to_log = self._l10n_it_edi_get_extra_info(company, document_type, tree, incoming=incoming)

            # Partner
            partner_info = buyer_seller_info[partner_role]
            vat = get_text(tree, partner_info['vat_xpath'])
            codice_fiscale = get_text(tree, partner_info['codice_fiscale_xpath'])
            email = get_text(tree, '//DatiTrasmissione//Email') if partner_info['role'] == 'seller' else ''
            destination_code = get_text(tree, "//CodiceDestinatario") if partner_info['role'] == 'buyer' else ''
            if partner := self._l10n_it_edi_search_partner(company, vat, codice_fiscale, email, destination_code):
                self.partner_id = partner
            else:
                message = Markup("<br/>").join((
                    _("Partner not found, useful informations from XML file:"),
                    self._compose_info_message(tree, partner_info['section_xpath'])
                ))
                message_to_log.append(message)

            # Payment code
            if payment_code := get_text(tree, './/DettaglioPagamento[1]/CodicePagamento'):
                self.payment_reference = payment_code

            # Document Number
            if number := get_text(tree, './/DatiGeneraliDocumento//Numero'):
                self.ref = number

            # Currency
            if currency_str := get_text(tree, './/DatiGeneraliDocumento/Divisa'):
                currency = self.env.ref('base.%s' % currency_str.upper(), raise_if_not_found=False)
                if currency != self.env.company.currency_id and currency.active:
                    self.currency_id = currency

            # Date
            if document_date := get_date(tree, './/DatiGeneraliDocumento/Data'):
                self.invoice_date = document_date
            else:
                message_to_log.append(_("Document date invalid in XML file: %s", document_date))

            # Stamp Duty
            if stamp_duty := get_text(tree, './/DatiGeneraliDocumento/DatiBollo/ImportoBollo'):
                self.l10n_it_stamp_duty = float(stamp_duty)

            # Comment
            for narration in get_text(tree, './/DatiGeneraliDocumento//Causale', many=True):
                self.narration = '%s%s<br/>' % (self.narration or '', narration)

            # Informations relative to the purchase order, the contract, the agreement,
            # the reception phase or invoices previously transmitted
            # <2.1.2> - <2.1.6>
            for document_type in ['DatiOrdineAcquisto', 'DatiContratto', 'DatiConvenzione', 'DatiRicezione', 'DatiFattureCollegate']:
                for element in tree.xpath('.//DatiGenerali/' + document_type):
                    message = Markup("{} {}<br/>{}").format(document_type, _("from XML file:"), self._compose_info_message(element, '.'))
                    message_to_log.append(message)

            #  Dati DDT. <2.1.8>
            if elements := tree.xpath('.//DatiGenerali/DatiDDT'):
                message = Markup("<br/>").join((
                    _("Transport informations from XML file:"),
                    self._compose_info_message(tree, './/DatiGenerali/DatiDDT')
                ))
                message_to_log.append(message)

            # Due date. <2.4.2.5>
            if due_date := get_date(tree, './/DatiPagamento/DettaglioPagamento/DataScadenzaPagamento'):
                self.invoice_date_due = fields.Date.to_string(due_date)
            else:
                message_to_log.append(_("Payment due date invalid in XML file: %s", str(due_date)))

            # Information related to the purchase order <2.1.2>
            if (po_refs := get_text(tree, '//DatiGenerali/DatiOrdineAcquisto/IdDocumento', many=True)):
                self.invoice_origin = ", ".join(po_refs)

            # Total amount. <2.4.2.6>
            if amount_total := sum(float(x) for x in get_text(tree, './/ImportoPagamento', many=True) if x):
                message_to_log.append(_("Total amount from the XML File: %s", amount_total))

            # l10n_it_payment_method
            if payment_method := get_text(data['xml_tree'], '//DatiPagamento/DettaglioPagamento/ModalitaPagamento'):
                if payment_method in self.env['account.payment.method.line']._get_l10n_it_payment_method_selection_code():
                    self.l10n_it_payment_method = payment_method

            # Bank account. <2.4.2.13>
            if self.move_type not in ('out_invoice', 'in_refund'):
                if acc_number := get_text(tree, './/DatiPagamento/DettaglioPagamento/IBAN'):
                    if self.partner_id and self.partner_id.commercial_partner_id:
                        bank = self.env['res.partner.bank'].search([
                            ('acc_number', '=', acc_number),
                            ('partner_id', '=', self.partner_id.commercial_partner_id.id),
                            ('company_id', 'in', [self.company_id.id, False])
                        ], order='company_id', limit=1)
                    else:
                        bank = self.env['res.partner.bank'].search([
                            ('acc_number', '=', acc_number),
                            ('company_id', 'in', [self.company_id.id, False])
                        ], order='company_id', limit=1)
                    if bank:
                        self.partner_bank_id = bank
                    else:
                        message = Markup("<br/>").join((
                            _("Bank account not found, useful informations from XML file:"),
                            self._compose_info_message(tree, [
                                './/DatiPagamento//Beneficiario',
                                './/DatiPagamento//IstitutoFinanziario',
                                './/DatiPagamento//IBAN',
                                './/DatiPagamento//ABI',
                                './/DatiPagamento//CAB',
                                './/DatiPagamento//BIC',
                                './/DatiPagamento//ModalitaPagamento'
                            ])
                        ))
                        message_to_log.append(message)
            elif elements := tree.xpath('.//DatiPagamento/DettaglioPagamento'):
                message = Markup("<br/>").join((
                    _("Bank account not found, useful informations from XML file:"),
                    self._compose_info_message(tree, './/DatiPagamento')
                ))
                message_to_log.append(message)

            # Invoice lines. <2.2.1>
            tag_name = './/DettaglioLinee' if not extra_info['simplified'] else './/DatiBeniServizi'
            for element in tree.xpath(tag_name):
                move_line = self.invoice_line_ids.create({
                    'move_id': self.id,
                    'tax_ids': [fields.Command.clear()]})
                if move_line:
                    message_to_log += self._l10n_it_edi_import_line(element, move_line, extra_info)

            attachment_vals = []
            for element in tree.xpath('.//Allegati'):
                raw_name = get_text(element, './/NomeAttachment') or ''
                raw_ext = get_text(element, './/FormatoAttachment') or ''
                attachment_vals.append((
                    f"{raw_name}.{raw_ext}" if raw_ext and not raw_name.casefold().endswith(raw_ext.casefold()) else raw_name,
                    b64decode(get_text(element, './/Attachment')),
                ))
            if attachment_vals:
                self.sudo().message_post(
                    body=(_("Attachments from XML")),
                    attachments=attachment_vals,
                )

            global_enasarco_lines = []
            for additional_data_element in tree.xpath('//AltriDatiGestionali'):
                data_kind = additional_data_element.xpath('./TipoDato')[0].text.lower()
                if data_kind == 'cassa-prev':
                    data_text = additional_data_element.xpath('./RiferimentoTesto')[0].text.lower()
                    if 'enasarco' in data_text or 'tc07' in data_text:
                        parent_element = additional_data_element.xpath('..')[0]
                        price_unit = get_float(parent_element, './PrezzoUnitario')
                        if price_unit == 0.0:
                            global_enasarco_lines.append(parent_element)

            if len(global_enasarco_lines) == 1:
                parent_element = global_enasarco_lines[0]
                enasarco_amount = get_float(parent_element, './AltriDatiGestionali/RiferimentoNumero')
                price_unit = get_float(parent_element, './PrezzoUnitario')
                base_amount = self._get_l10_it_edi_get_taxable_amount_from_summary_data(parent_element.xpath('..')[0])
                enasarco_percentage = -self.currency_id.round(enasarco_amount / base_amount * 100) if base_amount else 0.0
                type_tax_use_domain = [('type_tax_use', '=', 'purchase' if self.is_outbound(include_receipts=True) else 'sale')]
                domain = [('l10n_it_pension_fund_type', '=', 'TC07')] + type_tax_use_domain
                if enasarco_tax := self._l10n_it_edi_search_tax_for_import(self.company_id, enasarco_percentage, domain):
                    to_remove_index = int(get_float(parent_element, './NumeroLinea')) - 1
                    self.invoice_line_ids[to_remove_index].unlink()
                    self.invoice_line_ids.tax_ids |= enasarco_tax

            for message in message_to_log:
                self.sudo().message_post(body=message)
            return self