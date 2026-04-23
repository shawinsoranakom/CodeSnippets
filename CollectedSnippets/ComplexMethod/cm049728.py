def _l10n_tw_edi_prepare_item_list(self, json_data, is_allowance=False):
        self.ensure_one()
        item_list = []
        sale_amount = 0
        tax_amount = 0
        AccountTax = self.env['account.tax']
        tax_type, _, _ = self._l10n_tw_edi_determine_tax_types()
        for index, line in enumerate(self.invoice_line_ids.filtered(lambda line: line.display_type == "product"), start=1):
            base_line = self._prepare_product_base_line_for_taxes_computation(line)
            if is_allowance and self.reversed_entry_id.currency_id == self.currency_id:
                base_line['rate'] = self.reversed_entry_id.invoice_currency_rate  # replace the rate by the original invoice's rate
            AccountTax._add_tax_details_in_base_line(base_line, self.company_id)

            twd_excluded_amount = base_line['tax_details']['raw_total_excluded']
            twd_included_amount = base_line['tax_details']['raw_total_included']
            quantity = abs(line.quantity)

            if self.l10n_tw_edi_is_b2b:
                item_price = float_round(twd_excluded_amount / quantity, precision_rounding=0.01)
                item_amount = float_round(twd_excluded_amount, precision_rounding=0.01)
            else:
                if not is_allowance and line.tax_ids and not line.tax_ids[0].price_include:
                    item_price = float_round(twd_excluded_amount / quantity, precision_rounding=0.01)
                    item_amount = float_round(twd_excluded_amount, precision_rounding=0.01)
                else:
                    item_price = float_round(twd_included_amount / quantity, precision_rounding=0.01)
                    item_amount = float_round(twd_included_amount, precision_rounding=0.01)

                item_amount_taxed = float_round(twd_included_amount, precision_rounding=0.01)

            # For special tax, we use twd_included_amount
            if tax_type == "4":
                item_price = float_round(twd_included_amount / quantity, precision_rounding=0.01)
                item_amount = float_round(twd_included_amount, precision_rounding=0.01)

            # Set item sequence for each invoice line, the sequence cannot start from 0
            if not is_allowance:
                line.l10n_tw_edi_ecpay_item_sequence = index

            # ItemRemark is in TW Chinese Characters because the official document uses TW Chinese Characters
            if self.l10n_tw_edi_is_b2b and is_allowance:
                item_list.append({
                    "OriginalInvoiceNumber": self.l10n_tw_edi_ecpay_invoice_id,
                    "OriginalInvoiceDate": convert_utc_time_to_tw_time(self.l10n_tw_edi_invoice_create_date),
                    "OriginalSequenceNumber": line.l10n_tw_edi_ecpay_item_sequence,
                    "ItemName": line.name[:100],
                    "ItemCount": quantity,
                    "ItemPrice": item_price,
                    "ItemAmount": item_amount,
                })
            else:
                item_list.append({
                    "ItemSeq": line.l10n_tw_edi_ecpay_item_sequence,
                    "ItemName": line.name[:100],
                    "ItemCount": quantity,
                    "ItemWord": line.product_uom_id.name[:6] if line.product_uom_id else False,
                    "ItemPrice": item_price,
                    "ItemTaxType": line.tax_ids[0].l10n_tw_edi_tax_type if tax_type != "4" and line.tax_ids else "",
                    "ItemAmount": item_amount,
                    "ItemRemark": f"商品單位: {line.product_uom_id.name[:6]}" if line.product_uom_id else ""
                })
            if self.l10n_tw_edi_is_b2b:
                sale_amount += item_amount
                tax_amount += base_line["tax_details"]["taxes_data"][0]["raw_tax_amount"]
            else:
                sale_amount += item_amount_taxed

        # Sale amount adjustment
        amount_on_invoice = self.amount_untaxed_signed if self.l10n_tw_edi_is_b2b and tax_type != "4" else self.amount_total_signed
        difference = self.company_id.currency_id.round(sale_amount) - abs(amount_on_invoice)
        if difference != 0:
            item_list[-1]["ItemAmount"] -= difference
            item_list[-1]["ItemAmount"] = float_round(item_list[-1]["ItemAmount"], precision_rounding=0.01)
            item_list[-1]["ItemPrice"] = float_round(item_list[-1]["ItemAmount"] / item_list[-1]["ItemCount"], precision_rounding=0.01)
            sale_amount -= difference

        # Credit note adjustment
        if is_allowance:
            # Check if the credit note has exchange difference, we need to add it to the sale amount
            reconciled_partials = self._get_all_reconciled_invoice_partials()
            exchange_difference = sum(item["amount"] for item in reconciled_partials if item.get("is_exchange"))
            if exchange_difference and self.l10n_tw_edi_is_b2b and tax_type != "4":
                tax_rate = abs(self.amount_untaxed_signed) / abs(self.amount_total_signed)
                exchange_difference = self.company_id.currency_id.round(exchange_difference * tax_rate)  # Use untaxed amount for B2B and non special type credit notes
            if self.reversed_entry_id.invoice_currency_rate > self.invoice_currency_rate:
                exchange_difference = exchange_difference * -1  # Convert to negative if the exchange rate is lower than the original invoice rate
            item_list[-1]["ItemAmount"] += exchange_difference
            item_list[-1]["ItemAmount"] = float_round(item_list[-1]["ItemAmount"], precision_rounding=0.01)
            item_list[-1]["ItemPrice"] = float_round(item_list[-1]["ItemAmount"] / item_list[-1]["ItemCount"], precision_rounding=0.01)
            sale_amount += exchange_difference

        if self.l10n_tw_edi_is_b2b and is_allowance:
            json_data["Details"] = item_list
        else:
            json_data["Items"] = item_list

        if not is_allowance:
            json_data["SalesAmount"] = self.company_id.currency_id.round(sale_amount)
        else:
            if self.l10n_tw_edi_is_b2b:
                json_data["TotalAmount"] = self.company_id.currency_id.round(sale_amount)
            else:
                json_data["AllowanceAmount"] = self.company_id.currency_id.round(sale_amount)

        if self.l10n_tw_edi_is_b2b:
            json_data["TaxAmount"] = self.company_id.currency_id.round(tax_amount) if tax_type != "4" else 0