def _link_bom(self, bom):
        """ Links the given BoM to the MO. Assigns BoM's lines, by-products and operations
        to the corresponding MO's components, by-products and workorders.
        """
        self.ensure_one()
        product_qty = self.product_qty
        uom = self.product_uom_id
        moves_to_unlink = self.env['stock.move']
        workorders_to_unlink = self.env['mrp.workorder']
        # For draft MO, all the work will be done by compute methods.
        # For cancelled and done MO, we don't want to do anything more than assinging the BoM.
        if self.state == 'draft' and self.bom_id == bom:
            # Only remove manual lines (not coming from BoM)
            workorders_to_unlink = workorders_to_unlink.filtered(lambda w: not w.operation_id)
            # Empties `bom_id` field so when the BoM is reassigns to this field, depending computes
            # will be triggered (doesn't happen if the field's value doesn't change).
            self.bom_id = False
        if self.state in ['cancel', 'done', 'draft']:
            if self.state == 'draft':
                # Don't straight delete the moves/workorders to avoid to cancel the MO, those will
                # be deleted once the BoM is assigned (and thus after new moves/WO were created).
                moves_to_unlink = self.move_raw_ids
                workorders_to_unlink = self.workorder_ids
            self.bom_id = bom
            moves_to_unlink.exists().unlink()
            workorders_to_unlink.exists().unlink()
            if self.state == 'draft':
                # we reset the product_qty/uom when the bom is changed on a draft MO
                # change them back to the original value
                self.write({'product_qty': product_qty, 'product_uom_id': uom.id})
            return

        def operation_key_values(record):
            return tuple(record[key] for key in ('company_id', 'name', 'workcenter_id'))

        def filter_by_attributes(record, product=self.product_id):
            product_attribute_ids = product.product_template_attribute_value_ids.ids
            return not record.bom_product_template_attribute_value_ids or\
                   any(att_val.id in product_attribute_ids for att_val in record.bom_product_template_attribute_value_ids)

        ratio = self._get_ratio_between_mo_and_bom_quantities(bom)
        _dummy, bom_lines = bom.explode(self.product_id, bom.product_qty)
        bom_lines_by_id = defaultdict(lambda: [None, 0])
        for line, exploded_values in bom_lines:
            if filter_by_attributes(line, exploded_values['product']):
                key = (line.id, line.product_id.id)
                bom_lines_by_id[key][0] = line
                bom_lines_by_id[key][1] += exploded_values['qty'] / exploded_values['original_qty']
        bom_byproducts_by_id = {byproduct.id: byproduct for byproduct in bom.byproduct_ids.filtered(filter_by_attributes)}
        operations_by_id = {operation.id: operation for operation in bom.operation_ids.filtered(filter_by_attributes)}

        # Compares the BoM's operations to the MO's workorders.
        for workorder in self.workorder_ids:
            operation = operations_by_id.pop(workorder.operation_id.id, False)
            if not operation:
                for operation_id in operations_by_id:
                    _operation = operations_by_id[operation_id]
                    if operation_key_values(_operation) == operation_key_values(workorder):
                        operation = operations_by_id.pop(operation_id)
                        break
            if operation and workorder.operation_id != operation:
                workorder.operation_id = operation
            elif operation and workorder.operation_id == operation:
                if workorder.workcenter_id != operation.workcenter_id:
                    workorder.workcenter_id = operation.workcenter_id
                if workorder.name != operation.name:
                    workorder.name = operation.name
            elif workorder.operation_id and workorder.operation_id not in operations_by_id:
                workorders_to_unlink |= workorder
        # Creates a workorder for each remaining operation.
        workorders_values = []
        for operation in operations_by_id.values():
            workorder_vals = {
                'name': operation.name,
                'operation_id': operation.id,
                'product_uom_id': self.product_uom_id.id,
                'production_id': self.id,
                'state': 'blocked',
                'workcenter_id': operation.workcenter_id.id,
            }
            workorders_values.append(workorder_vals)
        self.workorder_ids += self.env['mrp.workorder'].create(workorders_values)

        # Compares the BoM's lines to the MO's components.
        for move_raw in self.move_raw_ids:
            bom_line, bom_qty = bom_lines_by_id.pop((move_raw.bom_line_id.id, move_raw.product_id.id), (False, None))
            # If the move isn't already linked to a BoM lines, search for a compatible line.
            if not bom_line:
                for _bom_line, _bom_qty in bom_lines_by_id.values():
                    if move_raw.product_id == _bom_line.product_id:
                        bom_line, bom_qty = bom_lines_by_id.pop((_bom_line.id, move_raw.product_id.id))
                        if bom_line:
                            break
            move_raw_qty = bom_line and move_raw.product_uom._compute_quantity(
                move_raw.product_uom_qty * ratio, bom_line.product_uom_id
            )
            if bom_line and (
                    not move_raw.bom_line_id or
                    move_raw.bom_line_id.bom_id != bom or
                    move_raw.operation_id != bom_line.operation_id or
                    bom_line.product_qty != move_raw_qty
                ):
                move_raw.bom_line_id = bom_line
                move_raw.product_id = bom_line.product_id
                move_raw.product_uom_qty = bom_qty / ratio
                move_raw.product_uom = bom_line.product_uom_id
                if move_raw.operation_id != bom_line.operation_id:
                    move_raw.operation_id = bom_line.operation_id
                    move_raw.workorder_id = self.workorder_ids.filtered(lambda wo: wo.operation_id == move_raw.operation_id)
                move_raw.manual_consumption = move_raw._determine_is_manual_consumption(bom_line)
            elif not bom_line:
                moves_to_unlink |= move_raw
        # Creates a raw moves for each remaining BoM's lines.
        raw_moves_values = []
        for bom_line, bom_qty in bom_lines_by_id.values():
            raw_move_vals = self._get_move_raw_values(
                bom_line.product_id,
                bom_qty / ratio,
                bom_line.product_uom_id,
                bom_line=bom_line
            )
            raw_moves_values.append(raw_move_vals)
        self.env['stock.move'].create(raw_moves_values)

        # Compares the BoM's and the MO's by-products.
        for move_byproduct in self.move_byproduct_ids:
            bom_byproduct = bom_byproducts_by_id.pop(move_byproduct.byproduct_id.id, False)
            if not bom_byproduct:
                for _bom_byproduct in bom_byproducts_by_id.values():
                    if move_byproduct.product_id == _bom_byproduct.product_id:
                        bom_byproduct = bom_byproducts_by_id.pop(_bom_byproduct.id)
                        break
            move_byproduct_qty = bom_byproduct and move_byproduct.product_uom._compute_quantity(
                move_byproduct.product_uom_qty * ratio, bom_byproduct.product_uom_id
            )
            if bom_byproduct and (
                    not move_byproduct.byproduct_id or
                    bom_byproduct.product_id != move_byproduct.product_id or
                    bom_byproduct.product_qty != move_byproduct_qty
                ):
                move_byproduct.byproduct_id = bom_byproduct
                move_byproduct.cost_share = bom_byproduct.cost_share
                move_byproduct.product_uom_qty = bom_byproduct.product_qty / ratio
                move_byproduct.product_uom = bom_byproduct.product_uom_id
            elif not bom_byproduct:
                moves_to_unlink |= move_byproduct
        # For each remaining BoM's by-product, creates a move finished.
        byproduct_values = []
        for bom_byproduct in bom_byproducts_by_id.values():
            qty = bom_byproduct.product_qty / ratio
            move_byproduct_vals = self._get_move_finished_values(
                bom_byproduct.product_id.id, qty, bom_byproduct.product_uom_id.id,
                bom_byproduct.operation_id.id, bom_byproduct.id, bom_byproduct.cost_share
            )
            byproduct_values.append(move_byproduct_vals)
        self.move_finished_ids += self.env['stock.move'].create(byproduct_values)

        if self.warehouse_id.manufacture_steps in ('pbm', 'pbm_sam'):
            moves_to_unlink.product_uom_qty = 0
        moves_to_unlink._action_cancel()
        moves_to_unlink.unlink()
        workorders_to_unlink.unlink()
        self.bom_id = bom