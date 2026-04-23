def _l10n_it_edi_import_line(self, element, move_line, extra_info=None):
        extra_info = extra_info or {}
        company = move_line.company_id
        partner = move_line.partner_id
        message_to_log = []
        predict_enabled = self._is_prediction_enabled()

        # Sequence.
        line_elements = element.xpath('.//NumeroLinea')
        if line_elements:
            move_line.sequence = int(line_elements[0].text)

        # Name.
        move_line.name = " ".join(get_text(element, './/Descrizione').split())

        # Product.
        company_domain = self.env['res.company']._check_company_domain(company)
        if elements_code := element.xpath('.//CodiceArticolo'):
            for element_code in elements_code:
                type_code = element_code.xpath('.//CodiceTipo')[0]
                code = element_code.xpath('.//CodiceValore')[0]
                product = self.env['product.product'].search(Domain.AND([company_domain, Domain('barcode', '=', code.text)]))
                if (product and type_code.text == 'EAN'):
                    move_line.product_id = product
                    break
                if partner:
                    product_supplier = self.env['product.supplierinfo'].search(Domain.AND([
                        company_domain,
                        Domain('partner_id', '=', partner.id),
                        Domain('product_code', '=', code.text),
                    ]), limit=2)
                    if product_supplier and len(product_supplier) == 1 and product_supplier.product_id:
                        move_line.product_id = product_supplier.product_id
                        break
            if not move_line.product_id:
                for element_code in elements_code:
                    code = element_code.xpath('.//CodiceValore')[0]
                    product = self.env['product.product'].search(Domain.AND([company_domain, Domain('default_code', '=', code.text)]), limit=2)
                    if product and len(product) == 1:
                        move_line.product_id = product
                        break

        # If no product is found, try to find a product that may be fitting
        if predict_enabled and not move_line.product_id:
            fitting_product = move_line._predict_product()
            if fitting_product:
                name = move_line.name
                move_line.product_id = fitting_product
                move_line.name = name

        if predict_enabled:
            # Fitting account for the line
            fitting_account = move_line._predict_account()
            if fitting_account:
                move_line.account_id = fitting_account

        # Quantity.
        move_line.quantity = float(get_text(element, './/Quantita') or '1')

        # Taxes
        percentage = None
        if not extra_info['simplified']:
            percentage = get_float(element, './/AliquotaIVA')
            move_line.price_unit = get_float(element, './/PrezzoUnitario')

            # This tax is supposed to be 23% but applied to only a portion (50% or 20%) of the base amount
            # It's implemented as -11.5% (for 50% base) or -4.6% (for 20% base) instead of -23%
            # We need to calculate the actual effective percentage based on the ImponibileImporto/PrezzoTotale ratio
            # Example:
            # - If base is 50% of total: -23% * 0.5 = -11.5% (actual tax rate)
            # - If base is 20% of total: -23% * 0.2 = -4.6% (actual tax rate)
            if percentage == -23.0 and (prezzo_totale := get_float(element, './/PrezzoTotale')):
                body_tree = element.xpath('//FatturaElettronicaBody')[0]
                for riepilogo in body_tree.xpath('.//DatiRiepilogo'):
                    if get_float(riepilogo, './/AliquotaIVA') == percentage and (imponibile := get_float(riepilogo, './/ImponibileImporto')):
                        percentage = -float_round(23.0 * (imponibile / prezzo_totale), 1)
                        break
        elif amount := get_float(element, './/Importo'):
            percentage = get_float(element, './/Aliquota')
            if not percentage and (tax_amount := get_float(element, './/Imposta')):
                percentage = round(tax_amount / (amount - tax_amount) * 100)
            move_line.price_unit = amount / (1 + percentage / 100)

        move_line.tax_ids = [Command.clear()]
        if percentage is not None:
            l10n_it_exempt_reason = get_text(element, './/Natura').upper() or False
            extra_domain = extra_info.get('type_tax_use_domain', [('type_tax_use', '=', 'purchase')])
            if move_line.product_id:
                extra_domain = list(extra_domain)
                tax_scope = 'service' if move_line.product_id.type == 'service' else 'consu'
                extra_domain += [('tax_scope', 'in', [tax_scope, False])]
            if tax := self._l10n_it_edi_search_tax_for_import(company, percentage, extra_domain, l10n_it_exempt_reason=l10n_it_exempt_reason):
                move_line.tax_ids |= tax
            else:
                message = Markup("<br/>").join((
                    _("Tax not found for line with description '%s'", move_line.name),
                    self._compose_info_message(element, '.')
                ))
                message_to_log.append(message)

        # If no taxes were found, try to find taxes that may be fitting
        if predict_enabled and not move_line.tax_ids:
            fitting_taxes = move_line._predict_taxes()
            if fitting_taxes:
                move_line.tax_ids = [Command.set(fitting_taxes)]

        # Discounts
        if (discounts := element.xpath('.//ScontoMaggiorazione')) and not float_is_zero(move_line.price_unit, precision_rounding=move_line.currency_id.rounding):
            current_unit_price = move_line.price_unit
            # We apply the discounts in the order they are found in the XML.
            # The first discount is applied to the unit price, the second to the result of the first, etc.
            # If the discount is a percentage, it is applied to the unit price.
            # If the discount is an amount, it is subtracted from the unit price.
            # If the computed amount is different than the expected one, we log a message.
            for discount in discounts:
                discount_type = get_text(discount, './/Tipo')
                discount_sign = -1 if discount_type == 'MG' else 1
                if (discount_percentage := get_float(discount, './/Percentuale')) and not float_is_zero(discount_percentage, precision_rounding=move_line.currency_id.rounding):
                    current_unit_price *= (100 - discount_sign * discount_percentage) / 100
                elif discount_amount := get_float(discount, './/Importo'):
                    current_unit_price -= discount_sign * discount_amount
            expected_total = get_float(element, './/PrezzoTotale')
            current_total = current_unit_price * move_line.quantity
            if float_compare(expected_total, current_total, precision_rounding=move_line.currency_id.rounding) != 0:
                message = Markup("<br/>").join((
                    _("The amount_total %(current_total)s is different than PrezzoTotale %(expected_total)s for '%(move_name)s'", current_total=current_total, expected_total=expected_total, move_name=move_line.name),
                    self._compose_info_message(element, '.')
                ))
                message_to_log.append(message)
            discount = 100 - (100 * current_unit_price) / move_line.price_unit
            move_line.discount = discount

        type_tax_use_domain = extra_info['type_tax_use_domain']

        # Eventually apply withholding
        for withholding_tax in extra_info.get('withholding_taxes', []):
            withholding_tags = element.xpath("Ritenuta")
            if withholding_tags and withholding_tags[0].text == 'SI':
                move_line.tax_ids |= withholding_tax

        if extra_info['simplified']:
            return message_to_log

        price_subtotal = move_line.price_unit
        company = move_line.company_id

        # Eventually apply pension_fund
        if pension_fund_tax := self._get_pension_fund_tax_for_line(element, extra_info):
            move_line.tax_ids |= pension_fund_tax

        # Eventually apply ENASARCO
        for other_data_element in element.xpath('.//AltriDatiGestionali'):
            data_kind_element = other_data_element.xpath("./TipoDato")
            text_element = other_data_element.xpath("./RiferimentoTesto")
            if not data_kind_element or not text_element:
                continue
            data_kind, data_text = data_kind_element[0].text.lower(), text_element[0].text.lower()
            if data_kind == 'cassa-prev' and ('enasarco' in data_text or 'tc07' in data_text):
                number_element = other_data_element.xpath("./RiferimentoNumero")
                if not number_element or not price_subtotal:
                    continue
                enasarco_amount = float(number_element[0].text)
                enasarco_percentage = -self.env.company.currency_id.round(enasarco_amount / price_subtotal * 100)
                enasarco_tax = self._l10n_it_edi_search_tax_for_import(
                    company,
                    enasarco_percentage,
                    [('l10n_it_pension_fund_type', '=', 'TC07')] + type_tax_use_domain)
                if enasarco_tax:
                    move_line.tax_ids |= enasarco_tax
                else:
                    message_to_log.append(Markup("%s<br/>%s") % (
                        _("Enasarco tax not found for line with description '%s'", move_line.name),
                        self.env['account.move']._compose_info_message(other_data_element, '.'),
                    ))

        return message_to_log