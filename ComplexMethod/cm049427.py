def _import_invoice_fill_lines(self, invoice, tree, ref_multiplier):
        lines = tree.xpath('.//InvoiceLine')
        logs = []
        vals_list = []
        for line in lines:
            line_vals = {'move_id': invoice.id}

            # ==== name ====
            if item_description := find_xml_value('.//ItemDescription', line):
                product = self._search_product_for_import(item_description)
                if product:
                    line_vals['product_id'] = product.id
                else:
                    logs.append(_("The product '%s' could not be found.", item_description))
                line_vals['name'] = item_description

            # ==== quantity ====
            line_vals['quantity'] = find_xml_value('.//Quantity', line) or 1

            # ==== price_unit ====
            price_unit = find_xml_value('.//UnitPriceWithoutTax', line)
            line_vals['price_unit'] = ref_multiplier * float(price_unit) if price_unit else 1.0

            # ==== discount ====
            discounts = line.xpath('.//DiscountRate')
            discount_rate = 0.0
            for discount in discounts:
                discount_rate += float(discount.text)

            charges = line.xpath('.//ChargeRate')
            charge_rate = 0.0
            for charge in charges:
                charge_rate += float(charge.text)

            discount_rate -= charge_rate
            line_vals['discount'] = discount_rate

            # ==== tax_ids ====
            taxes_withheld_nodes = line.xpath('.//TaxesWithheld/Tax')
            taxes_outputs_nodes = line.xpath('.//TaxesOutputs/Tax')
            is_purchase = invoice.move_type.startswith('in')
            tax_ids = []
            logs += self._import_fill_invoice_line_taxes(invoice, line_vals, tax_ids, taxes_outputs_nodes, False, is_purchase)
            logs += self._import_fill_invoice_line_taxes(invoice, line_vals, tax_ids, taxes_withheld_nodes, True, is_purchase)
            line_vals['tax_ids'] = [Command.set(tax_ids)]
            vals_list.append(line_vals)

        invoice.invoice_line_ids = self.env['account.move.line'].create(vals_list)
        return logs