def write(self, vals):
        if 'company_id' in vals:
            for lot in self:
                if lot.location_id.company_id and vals['company_id'] and lot.location_id.company_id.id != vals['company_id']:
                    raise UserError(_("You cannot change the company of a lot/serial number currently in a location belonging to another company."))
        if 'product_id' in vals and any(vals['product_id'] != lot.product_id.id for lot in self):
            move_lines = self.env['stock.move.line'].search([('lot_id', 'in', self.ids), ('product_id', '!=', vals['product_id'])])
            if move_lines:
                raise UserError(_(
                    'You are not allowed to change the product linked to a serial or lot number '
                    'if some stock moves have already been created with that number. '
                    'This would lead to inconsistencies in your stock.'
                ))
        return super().write(vals)