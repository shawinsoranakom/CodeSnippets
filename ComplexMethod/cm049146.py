def _match_purchase_orders(self, po_references, partner_id, amount_total, from_ocr, timeout):
        """Tries to match open purchase order lines with this invoice given the information we have.

        :param po_references: a list of potential purchase order references/names
        :param partner_id: the vendor id inferred from the vendor bill
        :param amount_total: the total amount of the vendor bill
        :param from_ocr: indicates whether this vendor bill was created from an OCR scan (less reliable)
        :param timeout: the max time the line matching algorithm can take before timing out
        :return: tuple (str, recordset, dict) containing:
            * the match method:
                * `total_match`: purchase order reference(s) and total amounts match perfectly
                * `subset_total_match`: a subset of the referenced purchase orders' lines matches the total amount of
                    this invoice (OCR only)
                * `po_match`: only the purchase order reference matches (OCR only)
                * `subset_match`: a subset of the referenced purchase orders' lines matches a subset of the invoice
                    lines based on unit prices (EDI only)
                * `no_match`: no result found
            * recordset of `purchase.order.line` containing purchase order lines matched with an invoice line
            * list of tuple containing every `purchase.order.line` id and its related `account.move.line`
        """

        common_domain = [
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'purchase'),
            ('invoice_status', 'in', ('to invoice', 'no'))
        ]

        matching_purchase_orders = self.env['purchase.order']

        # We have purchase order references in our vendor bill and a total amount.
        if po_references and amount_total:
            # We first try looking for purchase orders whose names match one of the purchase order references in the
            # vendor bill.
            matching_purchase_orders |= self.env['purchase.order'].search(
                common_domain + [('name', 'in', po_references)])

            if not matching_purchase_orders:
                # If not found, we try looking for purchase orders whose `partner_ref` field matches one of the
                # purchase order references in the vendor bill.
                matching_purchase_orders |= self.env['purchase.order'].search(
                    common_domain + [('partner_ref', 'in', po_references)])

            if matching_purchase_orders:
                # We found matching purchase orders and are extracting all purchase order lines together with their
                # amounts still to be invoiced.
                po_lines = [line for line in matching_purchase_orders.order_line if line.product_qty]
                po_lines_with_amount = [{
                    'line': line,
                    'amount_to_invoice': (1 - line.qty_invoiced / line.product_qty) * line.price_total,
                } for line in po_lines]

                # If the sum of all remaining amounts to be invoiced for these purchase orders' lines is within a
                # tolerance from the vendor bill total, we have a total match. We return all purchase order lines
                # summing up to this vendor bill's total (could be from multiple purchase orders).
                if (amount_total - TOLERANCE
                        < sum(line['amount_to_invoice'] for line in po_lines_with_amount)
                        < amount_total + TOLERANCE):
                    return 'total_match', matching_purchase_orders.order_line, None

                elif from_ocr:
                    # The invoice comes from an OCR scan.
                    # We try to match the invoice total with purchase order lines.
                    matching_po_lines = self._find_matching_subset_po_lines(
                        po_lines_with_amount, amount_total, timeout)
                    if matching_po_lines:
                        return 'subset_total_match', self.env['purchase.order.line'].union(*matching_po_lines), None
                    else:
                        # We did not find a match for the invoice total.
                        # We return all purchase order lines based only on the purchase order reference(s) in the
                        # vendor bill.
                        return 'po_match', matching_purchase_orders.order_line, None

                else:
                    # We have an invoice from an EDI document, so we try to match individual invoice lines with
                    # individual purchase order lines from referenced purchase orders.
                    matching_po_lines, matching_inv_lines = self._find_matching_po_and_inv_lines(
                        po_lines, self.invoice_line_ids, timeout)

                    if matching_po_lines:
                        # We found a subset of purchase order lines that match a subset of the vendor bill lines.
                        # We return the matching purchase order lines and vendor bill lines.
                        return ('subset_match',
                                self.env['purchase.order.line'].union(*matching_po_lines),
                                matching_inv_lines)

        # As a last resort we try matching a purchase order by vendor and total amount.
        if partner_id and amount_total:
            purchase_id_domain = common_domain + [
                ('partner_id', 'child_of', [partner_id]),
                ('amount_total', '>=', amount_total - TOLERANCE),
                ('amount_total', '<=', amount_total + TOLERANCE)
            ]
            matching_purchase_orders = self.env['purchase.order'].search(purchase_id_domain)
            if len(matching_purchase_orders) == 1:
                # We found exactly one match on vendor and total amount (within tolerance).
                # We return all purchase order lines of the purchase order whose total amount matched our vendor bill.
                return 'total_match', matching_purchase_orders.order_line, None

        # We couldn't find anything, so we return no lines.
        return ('no_match', matching_purchase_orders.order_line, None)