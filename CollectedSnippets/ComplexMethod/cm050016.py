def _get_ddt_values(self):
        """
        We calculate the link between the invoice lines and the deliveries related to the invoice through the
        links with the sale order(s).  We assume that the first picking was invoiced first. (FIFO)
        :return: a dictionary with as key the picking and value the invoice line numbers (by counting)
        """
        self.ensure_one()
        # We don't consider returns/credit notes as we suppose they will lead to more deliveries/invoices as well
        if self.move_type != "out_invoice" or self.state != 'posted':
            return {}
        line_count = 0
        invoice_line_pickings = {}
        for line in self.invoice_line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_subsection', 'line_note')):
            line_count += 1
            done_moves_related = line.sale_line_ids.mapped('move_ids').filtered(
                lambda m: m.state == 'done' and m.location_dest_id.usage == 'customer' and m.picking_type_id.code == 'outgoing')
            if len(done_moves_related) <= 1:
                if done_moves_related and line_count not in invoice_line_pickings.get(done_moves_related.picking_id, []):
                    invoice_line_pickings.setdefault(done_moves_related.picking_id, []).append(line_count)
            else:
                total_invoices = done_moves_related.mapped('sale_line_id.invoice_lines').filtered(
                    lambda l: l.move_id.state == 'posted' and l.move_id.move_type == 'out_invoice').sorted(lambda l: (l.move_id.invoice_date, l.move_id.id))
                total_invs = [(i.product_uom_id._compute_quantity(i.quantity, i.product_id.uom_id), i) for i in total_invoices]
                inv = total_invs.pop(0)
                # Match all moves and related invoice lines FIFO looking for when the matched invoice_line matches line
                for move in done_moves_related.sorted(lambda m: (m.date, m.id)):
                    rounding = move.product_uom.rounding
                    move_qty = move.product_qty
                    while (float_compare(move_qty, 0, precision_rounding=rounding) > 0):
                        if float_compare(inv[0], move_qty, precision_rounding=rounding) > 0:
                            inv = (inv[0] - move_qty, inv[1])
                            invoice_line = inv[1]
                            move_qty = 0
                        if float_compare(inv[0], move_qty, precision_rounding=rounding) <= 0:
                            move_qty -= inv[0]
                            invoice_line = inv[1]
                            if total_invs:
                                inv = total_invs.pop(0)
                            else:
                                move_qty = 0 #abort when not enough matched invoices
                        # If in our FIFO iteration we stumble upon the line we were checking
                        if invoice_line == line and line_count not in invoice_line_pickings.get(move.picking_id, []):
                            invoice_line_pickings.setdefault(move.picking_id, []).append(line_count)
        return invoice_line_pickings