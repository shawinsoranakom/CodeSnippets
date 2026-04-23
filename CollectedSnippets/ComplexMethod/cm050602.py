def _compute_l10n_it_edi_doi_warning(self):
        for move in self:
            move.l10n_it_edi_doi_warning = ''
            declaration = move.l10n_it_edi_doi_id

            show_warning = (
                declaration
                and move.is_sale_document(include_receipts=False)
                and move.state != 'cancel'
            )
            if not show_warning:
                continue

            declaration_invoiced = declaration.invoiced
            declaration_not_yet_invoiced = declaration.not_yet_invoiced
            if move.state != 'posted':  # exactly the 'posted' invoices are included in declaration.invoiced
                # Here we replicate what would happen when posting the invoice.
                # Note: lines manually added to a move linked to a sales order are not added to the sales order
                declaration_invoiced += move.l10n_it_edi_doi_amount
                additional_invoiced_qty = {}
                linked_orders = self.env['sale.order']
                for invoice_line in move.invoice_line_ids:
                    for sale_line in invoice_line.sale_line_ids:
                        order = sale_line.order_id
                        if order.l10n_it_edi_doi_id == declaration:
                            linked_orders |= order
                        qty_invoiced = invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, sale_line.product_uom_id) * -move.direction_sign
                        sale_line_id = sale_line.ids[0]  # do not just use `id` in case of NewId
                        additional_invoiced_qty[sale_line_id] = additional_invoiced_qty.get(sale_line_id, 0) + qty_invoiced
                for order in linked_orders:
                    not_yet_invoiced = order.l10n_it_edi_doi_not_yet_invoiced
                    not_yet_invoiced_after_posting = order._l10n_it_edi_doi_get_amount_not_yet_invoiced(
                        declaration,
                        additional_invoiced_qty=additional_invoiced_qty,
                    )
                    declaration_not_yet_invoiced -= not_yet_invoiced - not_yet_invoiced_after_posting

            validity_warnings = declaration._get_validity_warnings(
                move.company_id, move.commercial_partner_id, move.currency_id, move.l10n_it_edi_doi_date,
                invoiced_amount=declaration_invoiced,
            )

            threshold_warning = declaration._build_threshold_warning_message(declaration_invoiced, declaration_not_yet_invoiced)

            move.l10n_it_edi_doi_warning = '{}\n\n{}'.format('\n'.join(validity_warnings), threshold_warning).strip()