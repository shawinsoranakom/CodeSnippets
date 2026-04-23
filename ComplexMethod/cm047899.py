def _l10n_ke_cu_lines_messages(self):
        """ Serialise the data of each line on the invoice

        This function transforms the lines in order to handle the differences
        between the KRA expected data and the lines in odoo.

        If a discount line (as a negative line) has been added to the invoice
        lines, find a suitable line/lines to distribute the discount accross

        :returns: List of byte-strings representing each command <CMD> and the
                  <DATA> of the line, which will be sent to the fiscal device
                  in order to add a line to the opened invoice.
        """
        def is_discount_line(line):
            return line.price_subtotal < 0.0

        def is_candidate(discount_line, other_line):
            """ If the of one line match those of the discount line, the discount can be distributed accross that line """
            discount_taxes = discount_line.tax_ids.flatten_taxes_hierarchy()
            other_line_taxes = other_line.tax_ids.flatten_taxes_hierarchy()
            return set(discount_taxes.ids) == set(other_line_taxes.ids)

        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == 'product' and l.quantity and l.price_total)
        # The device expects all monetary values in Kenyan Shillings
        if self.currency_id == self.company_id.currency_id:
            currency_rate = 1
        # In the case of a refund, use the currency rate of the original invoice
        elif self.move_type == 'out_refund' and self.reversed_entry_id:
            currency_rate = abs(self.reversed_entry_id.amount_total_signed / self.reversed_entry_id.amount_total)
        else:
            currency_rate = abs(self.amount_total_signed / self.amount_total)

        discount_dict = {line.id: line.discount for line in lines if line.price_total > 0}
        for line in lines:
            if not is_discount_line(line):
                continue
            # Search for non-discount lines
            candidate_vals_list = [l for l in lines if not is_discount_line(l) and is_candidate(l, line)]
            candidate_vals_list = sorted(candidate_vals_list, key=lambda x: x.price_unit * x.quantity, reverse=True)
            line_to_discount = abs(line.price_unit * line.quantity)
            for candidate in candidate_vals_list:
                still_to_discount = abs(candidate.price_unit * candidate.quantity * (100.0 - discount_dict[candidate.id]) / 100.0)
                if line_to_discount >= still_to_discount:
                    discount_dict[candidate.id] = 100.0
                    line_to_discount -= still_to_discount
                else:
                    rest_to_discount = abs((line_to_discount / (candidate.price_unit * candidate.quantity)) * 100.0)
                    discount_dict[candidate.id] += rest_to_discount
                    break

        msgs = []
        tax_details = self._prepare_invoice_aggregated_taxes()
        for line in self.invoice_line_ids.filtered(lambda l: l.display_type == 'product' and l.quantity and l.price_total > 0 and not discount_dict.get(l.id) >= 100):
            # Here we use the original discount of the line, since it the distributed discount has not been applied in the price_total
            price_total = 0
            percentage = 0
            item_code = line.tax_ids[0].l10n_ke_item_code_id
            for tax in tax_details['tax_details_per_record'][line]['tax_details']:
                if tax.amount in (16, 8, 0):  # This should only occur once
                    line_tax_details = tax_details['tax_details_per_record'][line]['tax_details'][tax]
                    price_total = abs(line_tax_details['base_amount_currency']) + abs(line_tax_details['tax_amount_currency'])
                    percentage = tax.amount
            price = round(price_total / abs(line.quantity) * 100 / (100 - line.discount), line.currency_id.decimal_places) * currency_rate
            price = ('%.5f' % price).rstrip('0').rstrip('.')
            uom = line.product_uom_id and line.product_uom_id.name or ''

            line_data = b';'.join([
                self._l10n_ke_fmt(line.name, 36),                       # 36 symbols for the article's name
                self._l10n_ke_fmt(item_code.tax_rate or 'A', 1),        # 1 symbol for article's vat class ('A', 'B', 'C', 'D', or 'E')
                price[:15].encode('cp1251'),                    # 1 to 15 symbols for article's price with up to 5 digits after decimal point
                self._l10n_ke_fmt(uom, 3),                              # 3 symbols for unit of measure
                (item_code.code or '').ljust(10).encode('cp1251'),      # 10 symbols for KRA item code in the format xxxx.xx.xx (can be empty)
                self._l10n_ke_fmt(item_code.description or '', 20),     # 20 symbols for KRA item code description (can be empty)
                str(percentage).encode('cp1251')[:5]                    # up to 5 symbols for vat rate
            ])
            # 1 to 10 symbols for quantity
            line_data += b'*' + str(abs(line.quantity)).encode('cp1251')[:10]
            if discount_dict.get(line.id):
                # 1 to 7 symbols for percentage of discount/addition
                discount_sign = b'-' if discount_dict[line.id] > 0 else b'+'
                discount = discount_sign + str(abs(discount_dict[line.id])).encode('cp1251')[:6]
                line_data += b',' + discount + b'%'

            # Command: Sale of article (0x31)
            msgs += [b'\x31' + line_data]
        return msgs