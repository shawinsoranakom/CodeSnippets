def action_merge(self):
        self._pre_action_split_merge_hook(merge=True)
        products = set([(production.product_id, production.bom_id) for production in self])
        product_id, bom_id = products.pop()
        users = set([production.user_id for production in self])
        if len(users) == 1:
            user_id = users.pop()
        else:
            user_id = self.env.user

        origs = self._prepare_merge_orig_links()
        dests = {}
        for move in self.move_finished_ids:
            dests.setdefault(move.byproduct_id.id, []).extend(move.move_dest_ids.ids)

        production = self.env['mrp.production'].with_context(default_picking_type_id=self.picking_type_id.id).create({
            'product_id': product_id.id,
            'bom_id': bom_id.id,
            'picking_type_id': self.picking_type_id.id,
            'product_qty': sum(production.product_uom_qty for production in self),
            'product_uom_id': product_id.uom_id.id,
            'location_final_id': all(mo.location_final_id for mo in self) and len(self.location_final_id) == 1 and self.location_final_id.id,
            'user_id': user_id.id,
            'reference_ids': [Command.link(r.id) for r in self.reference_ids],
            'origin': ",".join(sorted([production.name for production in self])),
        })

        # update linked picking
        self.env['stock.move'].search([
            ('production_group_id', 'in', self.production_group_id.ids),
        ]).production_group_id = production.production_group_id

        # update linked mos
        production.production_group_id.parent_ids = [Command.set(self.production_group_id.parent_ids.ids)]
        production.production_group_id.child_ids = [Command.set(self.production_group_id.child_ids.ids)]

        for move in production.move_raw_ids:
            for field, vals in origs[move.bom_line_id.id].items():
                move[field] = vals

        for move in production.move_finished_ids:
            move.move_dest_ids = [Command.set(dests[move.byproduct_id.id])]

        self.move_dest_ids.created_production_id = production.id

        if 'confirmed' in self.mapped('state'):
            production.move_raw_ids._adjust_procure_method()
            (production.move_raw_ids | production.move_finished_ids).write({'state': 'confirmed'})
            production.action_confirm()

        self.with_context(skip_activity=True)._action_cancel()
        self.sudo().production_group_id.unlink()
        # set the new deadline of origin moves (stock to pre prod)
        production.move_raw_ids.move_orig_ids.with_context(date_deadline_propagate_ids=set(production.move_raw_ids.ids)).write({'date_deadline': production.date_start})
        for p in self:
            p._message_log(body=_('This production has been merge in %s', production.display_name))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': production.id,
        }