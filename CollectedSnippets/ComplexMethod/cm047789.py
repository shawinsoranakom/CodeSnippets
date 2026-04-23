def _compute_workorder_ids(self):
        for production in self:
            if production.state != 'draft':
                continue
            # we need to link the already existing wo's in case the relations are cleared but the wo are not deleted
            workorders_list = [Command.link(wo.id) for wo in production.workorder_ids.filtered(lambda wo: wo.ids)]
            relevant_boms = [exploded_boms[0] for exploded_boms in production.bom_id.explode(production.product_id, 1.0, picking_type=production.bom_id.picking_type_id)[0]]
            # we don't delete wo's that are not bom related nor related to a subom
            deleted_workorders_ids = production.workorder_ids.filtered(lambda wo: wo.operation_id and wo.operation_id.bom_id not in relevant_boms).mapped('id')
            workorders_list += [Command.delete(wo_id) for wo_id in deleted_workorders_ids]
            if not production.bom_id and not production._origin.product_id:
                production.workorder_ids = workorders_list
            # if the product has changed or if in a second onchange with bom resets the relations
            if production.product_id != production._origin.product_id \
                or (not production._origin.bom_id and production.bom_id) \
                or (production._origin.bom_id != production.bom_id and production._origin.bom_id.operation_ids and not production.workorder_ids.filtered(lambda wo: wo.ids and wo.operation_id)):
                production.workorder_ids = [Command.clear()]
            if production.bom_id and production.product_id and production.product_qty > 0:
                # keep manual entries
                workorders_values = []
                product_qty = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id)
                exploded_boms, _dummy = production.bom_id.explode(production.product_id, product_qty / production.bom_id.product_qty, picking_type=production.bom_id.picking_type_id,
                    never_attribute_values=production.never_product_template_attribute_value_ids)

                for bom, bom_data in exploded_boms:
                    # If the operations of the parent BoM and phantom BoM are the same, don't recreate work orders.
                    if not (bom.operation_ids and (not bom_data['parent_line'] or bom_data['parent_line'].bom_id.operation_ids != bom.operation_ids)):
                        continue
                    for operation in bom.operation_ids:
                        if operation._skip_operation_line(bom_data['product'] if not bom_data['parent_line'] else bom_data['parent_line']['product_id'], production.never_product_template_attribute_value_ids):
                            workorder = production.workorder_ids.filtered(lambda wo: wo.operation_id == operation and wo.operation_id.bom_id == bom)
                            if workorder:
                                # If for some reason a non-relevant workorder is still there, e.g. after a change in never_product_template_attribute_value_ids
                                workorders_list += [Command.delete(workorder.id)]
                            continue
                        workorders_values += [{
                            'name': operation.name,
                            'production_id': production.id,
                            'workcenter_id': operation.workcenter_id.id,
                            'product_uom_id': production.product_uom_id.id,
                            'operation_id': operation.id,
                            'state': 'ready',
                        }]
                workorders_dict = {wo.operation_id.id: wo for wo in production.workorder_ids.filtered(
                    lambda wo: wo.operation_id and wo.id not in deleted_workorders_ids)}
                for workorder_values in workorders_values:
                    if workorder_values['operation_id'] in workorders_dict:
                        # update existing entries
                        workorders_list += [Command.update(workorders_dict[workorder_values['operation_id']].id, workorder_values)]
                    else:
                        # add new entries
                        workorders_list += [Command.create(workorder_values)]
                production.workorder_ids = workorders_list
            else:
                production.workorder_ids = [Command.delete(wo_id) for wo_id in production.workorder_ids.filtered(lambda wo: wo.operation_id).mapped('id')]