def button_mark_done(self):
        res = self.pre_button_mark_done()
        if res is not True:
            return res

        if self.env.context.get('mo_ids_to_backorder'):
            productions_to_backorder = self.browse(self.env.context['mo_ids_to_backorder'])
            productions_not_to_backorder = self - productions_to_backorder
        else:
            productions_not_to_backorder = self
            productions_to_backorder = self.env['mrp.production']
        productions_not_to_backorder = productions_not_to_backorder.with_context(no_procurement=True)
        self.workorder_ids.button_finish()

        backorders = productions_to_backorder and productions_to_backorder._split_productions()
        backorders = backorders - productions_to_backorder

        productions_not_to_backorder._post_inventory(cancel_backorder=True)
        productions_to_backorder._post_inventory(cancel_backorder=True)

        # if completed products make other confirmed/partially_available moves available, assign them
        done_move_finished_ids = (productions_to_backorder.move_finished_ids | productions_not_to_backorder.move_finished_ids).filtered(lambda m: m.state == 'done')
        done_move_finished_ids._trigger_assign()

        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (productions_not_to_backorder.move_raw_ids | productions_not_to_backorder.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        for production in self:
            production.write({
                'date_finished': fields.Datetime.now(),
                'priority': '0',
                'is_locked': True,
                'state': 'done',
            })

        # It is prudent to reserve any quantity that has become available to the backorder
        # production's move_raw_ids after the production which spawned them has been marked done.
        backorders_to_assign = backorders.filtered(
            lambda order:
            order.picking_type_id.reservation_method == 'at_confirm'
        )
        for backorder in backorders_to_assign:
            backorder.action_assign()

        report_actions = self._get_autoprint_done_report_actions()
        if self.env.context.get('skip_redirection'):
            if report_actions:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'do_multi_print',
                    'context': {},
                    'params': {
                        'reports': report_actions,
                    }
                }
            return True
        another_action = False
        if not backorders:
            if self.env.context.get('from_workorder'):
                another_action = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.production',
                    'views': [[self.env.ref('mrp.mrp_production_form_view').id, 'form']],
                    'res_id': self.id,
                    'target': 'main',
                }
            elif self.env.user.has_group('mrp.group_mrp_reception_report'):
                mos_to_show = self.filtered(lambda mo: mo.picking_type_id.auto_show_reception_report)
                lines = mos_to_show.move_finished_ids.filtered(lambda m: m.product_id.is_storable and m.state != 'cancel' and m.picked and not m.move_dest_ids)
                if lines:
                    if any(mo.show_allocation for mo in mos_to_show):
                        another_action = mos_to_show.action_view_reception_report()
            if report_actions:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'do_multi_print',
                    'params': {
                        'reports': report_actions,
                        'anotherAction': another_action,
                    }
                }
            if another_action:
                return another_action
            return True
        context = {
            k: False if k.startswith('skip_') else v
            for k, v in self.env.context.items()
            if not k.startswith('default_')
        }
        another_action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'context': dict(context, mo_ids_to_backorder=None)
        }
        if len(backorders) == 1:
            another_action.update({
                'views': [[False, 'form']],
                'view_mode': 'form',
                'res_id': backorders[0].id,
            })
        else:
            another_action.update({
                'name': _("Backorder MO"),
                'domain': [('id', 'in', backorders.ids)],
                'views': [[False, 'list'], [False, 'form']],
                'view_mode': 'list,form',
            })
        if report_actions:
            return {
                'type': 'ir.actions.client',
                'tag': 'do_multi_print',
                'params': {
                    'reports': report_actions,
                    'anotherAction': another_action,
                }
            }
        return another_action