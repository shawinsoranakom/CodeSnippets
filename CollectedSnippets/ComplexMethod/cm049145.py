def _find_matching_po_and_inv_lines(self, po_lines, inv_lines, timeout):
        """Finds purchase order lines that match some of the invoice lines.

        We try to find a purchase order line for every invoice line matching on the unit price and having at least
        the same quantity to invoice.

        :param po_lines: list of purchase order lines that can be matched
        :param inv_lines: list of invoice lines to be matched
        :param timeout: how long this function can run before we consider it too long
        :return: a tuple (list, list) containing:
            * matched 'purchase.order.line'
            * tuple of purchase order line ids and their matched 'account.move.line'
        """
        # Sort the invoice lines by unit price and quantity to speed up matching
        invoice_lines = sorted(inv_lines, key=lambda line: (line.price_unit, line.quantity), reverse=True)
        # Sort the purchase order lines by unit price and remaining quantity to speed up matching
        purchase_lines = sorted(
            po_lines,
            key=lambda line: (line.price_unit, line.product_qty - line.qty_invoiced),
            reverse=True
        )
        matched_po_lines = []
        matched_inv_lines = []
        try:
            start_time = time.time()
            for invoice_line in invoice_lines:
                # There are no purchase order lines left. We are done matching.
                if not purchase_lines:
                    break
                # A dict of purchase lines mapping to a diff score for the name
                purchase_line_candidates = {}
                for purchase_line in purchase_lines:
                    if time.time() - start_time > timeout:
                        raise TimeoutError

                    # The lists are sorted by unit price descendingly.
                    # When the unit price of the purchase line is lower than the unit price of the invoice line,
                    # we cannot get a match anymore.
                    if purchase_line.price_unit < invoice_line.price_unit:
                        break

                    if (invoice_line.price_unit == purchase_line.price_unit
                            and invoice_line.quantity <= purchase_line.product_qty - purchase_line.qty_invoiced):
                        # The current purchase line is a possible match for the current invoice line.
                        # We calculate the name match ratio and continue with other possible matches.
                        #
                        # We could match on more fields coming from an EDI invoice, but that requires extending the
                        # account.move.line model with the extra matching fields and extending the EDI extraction
                        # logic to fill these new fields.
                        purchase_line_candidates[purchase_line] = difflib.SequenceMatcher(
                            None, invoice_line.name, purchase_line.name).ratio()

                if len(purchase_line_candidates) > 0:
                    # We take the best match based on the name.
                    purchase_line_match = max(purchase_line_candidates, key=purchase_line_candidates.get)
                    if purchase_line_match:
                        # We found a match. We remove the purchase order line so it does not get matched twice.
                        purchase_lines.remove(purchase_line_match)
                        matched_po_lines.append(purchase_line_match)
                        matched_inv_lines.append((purchase_line_match.id, invoice_line))

            return (matched_po_lines, matched_inv_lines)

        except TimeoutError:
            _logger.warning('Timed out during search of matching purchase order lines')
            return ([], [])