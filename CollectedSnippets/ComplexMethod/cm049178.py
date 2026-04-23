def _subcontracted_produce(self, subcontract_details):
        self.ensure_one()
        group_by_company = defaultdict(lambda: ([], []))
        for move, bom in subcontract_details:
            if move.move_orig_ids.production_id:
                if len(move.move_orig_ids.move_dest_ids) > 1:
                    # Magic spicy sauce for the backorder case:
                    # To ensure correct splitting of the component moves of the SBC MO, we will invoke a split of the SBC
                    # MO here directly and then link the backorder MO to the backorder move.
                    # If we would just run _subcontracted_produce as usual for the newly created SBC receipt move, any
                    # reservations of raw component moves of the SBC MO would not be preserved properly (for example when
                    # using resupply subcontractor on order)
                    production_to_split = move.move_orig_ids[0].production_id
                    original_qty = move.move_orig_ids[0].product_qty
                    move.move_orig_ids = False
                    _, new_mo = production_to_split.with_context(allow_more=True)._split_productions({production_to_split: [original_qty, move.product_qty]})
                    new_mo.move_finished_ids.move_dest_ids = move
                    continue
                else:
                    # do not create extra production for move that have their quantity updated
                    return
            quantity = move.product_qty or move.quantity
            if move.product_uom.compare(quantity, 0) <= 0:
                # If a subcontracted amount is decreased, don't create a MO that would be for a negative value.
                continue

            mo_subcontract = self._prepare_subcontract_mo_vals(move, bom)
            # Group the MO by company
            group_by_company[move.company_id.id][0].append(mo_subcontract)
            group_by_company[move.company_id.id][1].append(move)

        for company, group in group_by_company.items():
            vals_list, moves = group
            grouped_mo = self.env['mrp.production'].with_company(company).create(vals_list)
            grouped_mo.with_context(self._get_subcontract_mo_confirmation_ctx()).action_confirm()
            for mo, move in zip(grouped_mo, moves):
                mo.date_finished = move.date
                finished_move = mo.move_finished_ids.filtered(lambda m: m.product_id == move.product_id)
                finished_move.move_dest_ids = [Command.link(move.id)]
            grouped_mo.action_assign()