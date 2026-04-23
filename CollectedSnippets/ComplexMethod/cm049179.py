def _action_confirm(self, merge=True, merge_into=False, create_proc=True):
        subcontract_details_per_picking = defaultdict(list)
        for move in self:
            if move.location_id.usage != 'supplier' or move.location_dest_id.usage == 'supplier':
                continue
            if move.move_orig_ids.production_id:
                continue
            bom = move._get_subcontract_bom()
            if not bom:
                continue
            company = move.company_id
            subcontracting_location = \
                move.picking_id.partner_id.with_company(company).property_stock_subcontractor \
                or company.subcontracting_location_id
            move.write({
                'production_group_id': False,
                'is_subcontract': True,
                'location_id': subcontracting_location.id
            })
            move._action_assign()  # Re-reserve as the write on location_id will break the link
        res = super()._action_confirm(merge=merge, merge_into=merge_into, create_proc=create_proc)
        for move in res:
            if move.is_subcontract:
                subcontract_details_per_picking[move.picking_id].append((move, move._get_subcontract_bom()))
        for picking, subcontract_details in subcontract_details_per_picking.items():
            picking._subcontracted_produce(subcontract_details)

        if subcontract_details_per_picking:
            self.env['stock.picking'].concat(*list(subcontract_details_per_picking.keys())).action_assign()
        return res