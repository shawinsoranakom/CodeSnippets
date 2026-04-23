def _sync_subcontracting_productions(self):
        """
            Enforce the relationship between subcontracting receipt moves and their respective subcontracting productions.
            * For untracked moves:
                * There will always be only 1 production.
                * Updating the move quantity will update the production quantity.
            * For tracked moves:
                * There will be 1 production for every lot on this move.
                * This method will enforce the synchronisation between the total quantity per lot on the move and the linked productions.
                * The split mechanism for productions will be used to create new subcontracting MOs.
                * We take care to always keep at least 1 subcontracting production linked to the subcontracting receipt.
                  This ensures there will always be a production available for splitting.
        """
        for move in self:
            productions = move._get_subcontract_production()
            if not productions:
                continue
            if move.has_tracking == 'none':
                if productions.product_uom_id.compare(productions.product_qty, move.quantity) != 0:
                    self.sudo().env['change.production.qty'].with_context(skip_activity=True).create([{
                        'mo_id': productions.id,
                        'product_qty': move.quantity or move.product_uom_qty,
                    }]).change_prod_qty()
                    productions.action_assign()
            else:
                qty_by_lot = dict(move.move_line_ids._read_group([('move_id', '=', move.id)], ['lot_id'], ['quantity_product_uom:sum']))
                mos_to_assign = self.env['mrp.production']

                # 1. Ensure quantities of linked MOs still match the quantities on the move
                mos_to_create = {}  # lot -> qty
                for lot_id, ml_qty in qty_by_lot.items():
                    lot_mo = productions.filtered(lambda p: (p.lot_producing_ids and p.lot_producing_ids[0] == lot_id) or (not lot_id and not p.lot_producing_ids))
                    if not lot_mo:
                        mos_to_create[lot_id] = ml_qty
                    elif lot_mo.product_uom_id.compare(lot_mo.product_qty, ml_qty) != 0:
                        self.sudo().env['change.production.qty'].with_context(skip_activity=True).create([{
                            'mo_id': lot_mo.id,
                            'product_qty': ml_qty
                        }]).change_prod_qty()
                        mos_to_assign |= lot_mo

                # 2. Create new MOs where needed, by splitting them from an existing subcontracting MO
                if mos_to_create:
                    production_to_split = move._get_subcontract_production()[0]
                    new_mos = production_to_split.sudo().with_context(allow_more=True, mrp_subcontracting=False)._split_productions({
                        production_to_split: [production_to_split.product_qty] + list(mos_to_create.values())
                    }, cancel_remaining_qty=True)[1:]
                    mos_to_assign |= new_mos
                    for mo, lot_id in zip(new_mos, mos_to_create.keys()):
                        mo.lot_producing_ids = lot_id

                # 3. Delete 'orphan' MOs with lot not linked to any move line
                productions = move._get_subcontract_production()
                orphan_productions = productions.filtered(lambda p: (p.lot_producing_ids and p.lot_producing_ids[0] not in qty_by_lot) or (not p.lot_producing_ids and self.env['stock.lot'] not in qty_by_lot))
                if len(productions) == len(orphan_productions):
                    # Make sure not to delete all MOs, leave 1 subcontracting MO as 'open' MO for splitting later
                    production_to_keep = orphan_productions[-1]
                    production_to_keep.lot_producing_ids = False
                    orphan_productions = orphan_productions[:-1]
                if orphan_productions:
                    orphan_productions.sudo().with_context(skip_activity=True).unlink()
                    productions -= orphan_productions

                mos_to_assign.sudo().action_assign()