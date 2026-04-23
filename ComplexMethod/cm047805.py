def _action_cancel(self):
        documents_by_production = {}
        for production in self:
            documents = defaultdict(list)
            for move_raw_id in production.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                iterate_key = self._get_document_iterate_key(move_raw_id)
                if iterate_key:
                    document = self.env['stock.picking']._log_activity_get_documents({move_raw_id: (move_raw_id.product_uom_qty, 0)}, iterate_key, 'UP')
                    for key, value in document.items():
                        documents[key] += [value]
            if documents:
                documents_by_production[production] = documents
            if self.env.context.get('skip_activity'):
                continue
            # log an activity on Parent MO if child MO is cancelled.
            finish_moves = production.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            if finish_moves:
                production._log_downside_manufactured_quantity({finish_move: (production.product_uom_qty, 0.0) for finish_move in finish_moves}, cancel=True)

        if self._has_workorders():
            self.workorder_ids.filtered(lambda x: x.state not in ['done', 'cancel']).action_cancel()
        finish_moves = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        raw_moves = self.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        (finish_moves | raw_moves).with_context(skip_mo_check=True)._action_cancel()
        picking_ids = self.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and not (x.move_ids.move_dest_ids or any(mo.state == 'done' for mo in x.production_ids)))
        picking_ids.action_cancel()

        for production, documents in documents_by_production.items():
            filtered_documents = {}
            for (parent, responsible), rendering_context in documents.items():
                if not parent or parent._name == 'stock.picking' and parent.state == 'cancel' or parent == production:
                    continue
                filtered_documents[(parent, responsible)] = rendering_context
            production._log_manufacture_exception(filtered_documents, cancel=True)

        # In case of a flexible BOM, we don't know from the state of the moves if the MO should
        # remain in progress or done. Indeed, if all moves are done/cancel but the quantity produced
        # is lower than expected, it might mean:
        # - we have used all components but we still want to produce the quantity expected
        # - we have used all components and we won't be able to produce the last units
        #
        # However, if the user clicks on 'Cancel', it is expected that the MO is either done or
        # canceled. If the MO is still in progress at this point, it means that the move raws
        # are either all done or a mix of done / canceled => the MO should be done.
        mos_to_mark_as_done = self.filtered(lambda p: p.state not in ['done', 'cancel'] and p.bom_id.consumption == 'flexible')
        if mos_to_mark_as_done:
            mos_to_mark_as_done.write({'state': 'done'})

        return True