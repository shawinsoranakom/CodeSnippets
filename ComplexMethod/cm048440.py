def write(self, vals):
        if 'company_id' in vals:
            for picking_type in self:
                if picking_type.company_id.id != vals['company_id']:
                    raise UserError(_("Changing the company of this record is forbidden at this point, you should rather archive it and create a new one."))
        if 'sequence_code' in vals:
            for picking_type in self:
                if picking_type.warehouse_id:
                    picking_type.sequence_id.sudo().write({
                        'name': _('%(warehouse)s Sequence %(code)s', warehouse=picking_type.warehouse_id.name, code=vals['sequence_code']),
                        'prefix': picking_type.warehouse_id.code + '/' + vals['sequence_code'] + '/', 'padding': 5,
                        'company_id': picking_type.warehouse_id.company_id.id,
                    })
                else:
                    picking_type.sequence_id.sudo().write({
                        'name': _('Sequence %(code)s', code=vals['sequence_code']),
                        'prefix': vals['sequence_code'], 'padding': 5,
                        'company_id': picking_type.env.company.id,
                    })
        if 'reservation_method' in vals:
            if vals['reservation_method'] == 'by_date':
                if picking_types := self.filtered(lambda p: p.reservation_method != 'by_date'):
                    domain = [('picking_type_id', 'in', picking_types.ids), ('state', 'in', ('draft', 'confirmed', 'waiting', 'partially_available'))]
                    group_by = ['picking_type_id']
                    aggregates = ['id:recordset']
                    for picking_type, moves in self.env['stock.move']._read_group(domain, group_by, aggregates):
                        common_days = vals.get('reservation_days_before') or picking_type.reservation_days_before
                        priority_days = vals.get('reservation_days_before_priority') or picking_type.reservation_days_before_priority
                        for move in moves:
                            move.reservation_date = fields.Date.to_date(move.date) - timedelta(days=priority_days if move.priority == '1' else common_days)
            else:
                if picking_types := self.filtered(lambda p: p.reservation_method == 'by_date'):
                    moves = self.env['stock.move'].search([('picking_type_id', 'in', picking_types.ids), ('state', 'not in', ('assigned', 'done', 'cancel'))])
                    moves.reservation_date = False

        return super().write(vals)