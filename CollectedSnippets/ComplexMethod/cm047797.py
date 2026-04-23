def create(self, vals_list):
        for vals in vals_list:
            # Remove from `move_finished_ids` the by-product moves and then move `move_byproduct_ids`
            # into `move_finished_ids` to avoid duplicate and inconsistency.
            if vals.get('move_finished_ids', False) and vals.get('move_byproduct_ids', False):
                vals['move_finished_ids'] = list(filter(lambda move: move[2]['product_id'] == vals['product_id'], vals['move_finished_ids']))
                vals['move_finished_ids'] = vals.get('move_finished_ids', []) + vals['move_byproduct_ids']
                del vals['move_byproduct_ids']
            if not vals.get('name', False) or vals['name'] == _('New'):
                picking_type_id = vals.get('picking_type_id')
                if not picking_type_id:
                    picking_type_id = self._get_default_picking_type_id(vals.get('company_id', self.env.company.id))
                    vals['picking_type_id'] = picking_type_id
                vals['name'] = self.env['stock.picking.type'].browse(picking_type_id).sequence_id.next_by_id()
            if not vals.get('production_group_id'):
                vals['production_group_id'] = self.env["mrp.production.group"].create({'name': vals['name']}).id
        res = super().create(vals_list)
        # Make sure that the date passed in vals_list are taken into account and not modified by a compute
        reference_vals_list = []
        for rec, vals in zip(res, vals_list):
            (rec.move_raw_ids | rec.move_finished_ids).production_group_id = rec.production_group_id
            if not rec.reference_ids:
                reference_vals_list.append({
                    'name': rec.name,
                    'production_ids': [Command.set(rec.ids)],
                    'move_ids': [Command.set(rec.move_raw_ids.ids + rec.move_finished_ids.ids)],
                })
            if (rec.move_raw_ids
                and rec.move_raw_ids[0].date
                and vals.get('date_start')
                and rec.move_raw_ids[0].date != vals['date_start']):
                rec.move_raw_ids.write({
                    'date': vals['date_start'],
                    'date_deadline': vals['date_start']
                })
            if (rec.move_finished_ids
                and rec.move_finished_ids[0].date
                and vals.get('date_finished')
                and rec.move_finished_ids[0].date != vals['date_finished']):
                rec.move_finished_ids.write({'date': vals['date_finished']})
            elif (rec.move_finished_ids
                  and rec.date_finished
                  and rec.move_finished_ids[0].date != rec.date_finished
                  and not vals.get('date_finished')):
                # if no value is specified, do take the workorder duration (etc) into account
                rec.move_finished_ids.write({'date': rec.date_finished})
        if reference_vals_list:
            self.env['stock.reference'].create(reference_vals_list)
        return res