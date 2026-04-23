def _compute_is_storno(self):
        for line in self:
            if not line.company_id.account_storno:
                continue
            line.is_storno = (line.is_storno or line.move_id.is_storno) and line.move_type not in ('in_invoice', 'out_invoice')

            # For invoice lines, we want to set is_storno based on the sign of the line if the entire move is not storno (not refund)
            # This allows setting is_storno to true or false depending on quantity and price_unit
            if not line.move_id.is_storno and line in line.move_id.invoice_line_ids and line.quantity * line.price_unit:
                line.is_storno = line.quantity * line.price_unit < 0