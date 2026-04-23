def write(self, vals):
        if self.env.user._is_portal() and not self.env.su:
            unauthorized_fields = set(vals.keys()) - set(self._get_writeable_fields_portal_user())
            if unauthorized_fields:
                raise AccessError(_("You cannot write on fields %s in mrp.production.", ', '.join(unauthorized_fields)))

        if 'date_start' in vals and self.env.context.get('from_subcontract'):
            date_start = fields.Datetime.to_datetime(vals['date_start'])
            date_start_map = {
                prod: date_start - timedelta(days=prod.bom_id.produce_delay)
                if prod.bom_id else date_start
                for prod in self
            }
            res = True
            for production in self:
                res &= super(MrpProduction, production).write({**vals, 'date_start': date_start_map[production]})
            return res

        old_lots = [mo.lot_producing_ids for mo in self]
        if self.env.context.get('mrp_subcontracting') and 'product_qty' in vals:
            for mo in self:
                self.sudo().env['change.production.qty'].with_context(skip_activity=True, mrp_subcontracting=False, no_procurement=True).create([{
                    'mo_id': mo.id,
                    'product_qty': vals['product_qty'],
                }]).change_prod_qty()
                mo.sudo().action_assign()

        res = super().write(vals)

        if self.env.context.get('mrp_subcontracting') and ('product_qty' in vals or 'lot_producing_ids' in vals):
            for mo, old_lot in zip(self, old_lots):
                sbc_move = mo._get_subcontract_move()
                if not sbc_move:
                    continue
                if mo.product_tracking in ('lot', 'serial'):
                    sbc_move_lines = sbc_move.move_line_ids.filtered(lambda m: m.lot_id == old_lot)
                    sbc_move_line = sbc_move_lines[0]
                    sbc_move_line.quantity = mo.product_qty
                    sbc_move_line.lot_id = mo.lot_producing_ids
                    sbc_move_lines[1:].unlink()
                else:
                    sbc_move.quantity = mo.product_qty

        return res