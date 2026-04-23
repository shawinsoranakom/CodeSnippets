def _l10n_it_edi_doi_get_amount_not_yet_invoiced(self, declaration, additional_invoiced_qty=None):
        """
        Consider sales orders in self that use declaration of intent `declaration`.
        For each sales order we compute the amount that is tax exempt due to the declaration of intent
        (line has special declaration of intent tax applied) but not yet invoiced.
        For each line of the SO we i.e. use the not yet invoiced quantity to compute this amount.
        The aforementioned quantity is computed from field `qty_invoiced_posted` and parameter `additional_invoiced_qty`
        Return the sum of all these amounts on the SOs.
        :param declaration:             We only consider sales orders using Declaration of Intent `declaration`.
        :param additional_invoiced_qty: Dictionary (sale order line id -> float)
                                        The float represents additional invoiced amount qty for the sale order.
                                        This can i.e. be used to simulate posting an already linked invoice.
        """
        if not declaration:
            return 0

        if additional_invoiced_qty is None:
            additional_invoiced_qty = {}

        tax = declaration.company_id.l10n_it_edi_doi_tax_id
        if not tax:
            return 0

        not_yet_invoiced = 0
        for order in self:
            if declaration != order.l10n_it_edi_doi_id:
                continue

            order_lines = order.order_line.filtered(
                # The declaration tax cannot be used with other taxes on a single line
                # (checked in `action_confirm`)
                lambda line: line.tax_ids.ids == tax.ids
            )
            order_not_yet_invoiced = 0
            for line in order_lines:
                price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                qty_invoiced = line.qty_invoiced_posted
                if line.ids and additional_invoiced_qty:
                    qty_invoiced += additional_invoiced_qty.get(line.ids[0], 0)
                qty_to_invoice = line.product_uom_qty - qty_invoiced
                order_not_yet_invoiced += price_reduce * qty_to_invoice
            if declaration.currency_id.compare_amounts(order_not_yet_invoiced, 0) > 0:
                not_yet_invoiced += order_not_yet_invoiced

        return not_yet_invoiced