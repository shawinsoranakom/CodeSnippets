def _find_and_set_purchase_orders(self, po_references, partner_id, amount_total, from_ocr=False, timeout=10):
        """Finds related purchase orders that (partially) match the vendor bill and links the matching lines on this
        vendor bill.

        :param po_references: a list of potential purchase order references/names
        :param partner_id: the vendor id matched on the vendor bill
        :param amount_total: the total amount of the vendor bill
        :param from_ocr: indicates whether this vendor bill was created from an OCR scan (less reliable)
        :param timeout: the max time the line matching algorithm can take before timing out
        """
        self.ensure_one()

        method, matched_po_lines, matched_inv_lines = self._match_purchase_orders(
            po_references, partner_id, amount_total, from_ocr, timeout
        )

        if method in ('total_match', 'po_match'):
            # The purchase order reference(s) and total amounts match perfectly or there is only one purchase order
            # reference that matches with an OCR invoice. We replace the invoice lines with the purchase order lines.
            self._set_purchase_orders(matched_po_lines.order_id, force_write=True)

        elif method == 'subset_total_match':
            # A subset of the referenced purchase order lines matches the total amount of this invoice.
            # We keep the invoice lines, but add all the lines from the partially matched purchase orders:
            #   * "naively" matched purchase order lines keep their quantity
            #   * unmatched purchase order lines are added with their quantity set to 0
            self._set_purchase_orders(matched_po_lines.order_id, force_write=False)

            with self._get_edi_creation() as invoice:
                unmatched_lines = invoice.invoice_line_ids.filtered(
                    lambda l: l.purchase_line_id and l.purchase_line_id not in matched_po_lines)
                invoice.invoice_line_ids = [Command.update(line.id, {'quantity': 0}) for line in unmatched_lines]

        elif method == 'subset_match':
            # A subset of the referenced purchase order lines matches a subset of the invoice lines.
            # We add the purchase order lines, but adjust the quantity to the quantities in the invoice.
            # The original invoice lines that correspond with a purchase order line are removed.
            self._set_purchase_orders(matched_po_lines.order_id, force_write=False)

            with self._get_edi_creation() as invoice:
                unmatched_lines = invoice.invoice_line_ids.filtered(
                    lambda l: l.purchase_line_id and l.purchase_line_id not in matched_po_lines)
                invoice.invoice_line_ids = [Command.delete(line.id) for line in unmatched_lines]

                # We remove the original matched invoice lines and apply their quantities and taxes to the matched
                # purchase order lines.
                inv_and_po_lines = list(map(lambda line: (
                        invoice.invoice_line_ids.filtered(
                            lambda l: l.purchase_line_id and l.purchase_line_id.id == line[0]),
                        invoice.invoice_line_ids.filtered(
                            lambda l: l in line[1])
                    ),
                    matched_inv_lines
                ))
                invoice.invoice_line_ids = [
                    Command.update(po_line.id, {'quantity': inv_line.quantity, 'tax_ids': inv_line.tax_ids})
                    for po_line, inv_line in inv_and_po_lines
                ]
                invoice.invoice_line_ids = [Command.delete(inv_line.id) for dummy, inv_line in inv_and_po_lines]

                # If there are lines left not linked to a purchase order, we add a header
                unmatched_lines = invoice.invoice_line_ids.filtered(lambda l: not l.purchase_line_id)
                if len(unmatched_lines) > 0:
                    invoice.invoice_line_ids = [Command.create({
                        'display_type': 'line_section',
                        'name': _('From Electronic Document'),
                        'sequence': -1,
                    })]

        if not any(line.purchase_order_id for line in self.line_ids):
            self.invoice_origin = False