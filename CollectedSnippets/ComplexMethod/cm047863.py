def _get_operation_line(self, product, bom, qty, level, index, bom_report_line, simulated_leaves_per_workcenter):
        operations = []
        company = bom.company_id or self.env.company
        operations_planning = {}
        if bom_report_line['availability_state'] in ['unavailable', 'estimated'] and bom.operation_ids:
            qty_requested = bom.product_uom_id._compute_quantity(qty, bom.product_tmpl_id.uom_id)
            qty_to_produce = bom.product_tmpl_id.uom_id._compute_quantity(max(0, qty_requested - (product.virtual_available if level > 1 else 0)), bom.product_uom_id)
            if not (product or bom.product_tmpl_id).uom_id.is_zero(qty_to_produce):
                max_component_delay = 0
                for component in bom_report_line['components']:
                    line_delay = component.get('availability_delay', 0)
                    max_component_delay = max(max_component_delay, line_delay)
                date_today = self.env.context.get('from_date', fields.Date.today()) + timedelta(days=max_component_delay)
                operations_planning = self._simulate_bom_planning(bom, product, datetime.combine(date_today, time.min), qty_to_produce, simulated_leaves_per_workcenter=simulated_leaves_per_workcenter)
                bom_report_line['simulated'] = True
                bom_report_line['max_component_delay'] = max_component_delay
        operation_index = 0
        for operation in bom.operation_ids:
            if not product or operation._skip_operation_line(product):
                continue
            op = operation.with_context(product=product, quantity=qty)
            duration_expected = op.time_total
            bom_cost = self.env.company.currency_id.round(op.cost)
            if planning := operations_planning.get(operation, None):
                availability_state = 'estimated'
                availability_delay = (planning['date_finished'].date() - date_today).days
                availability_display = _('Estimated %s', format_date(self.env, planning['date_finished'])) + (" [" + planning['workcenter'].name + "]" if planning['workcenter'] != operation.workcenter_id else "")
            else:
                availability_state = 'available'
                availability_delay = 0
                availability_display = ''
            operations.append({
                'type': 'operation',
                'index': f"{index}{operation_index}",
                'level': level or 0,
                'operation': operation,
                'link_id': operation.id,
                'link_model': 'mrp.routing.workcenter',
                'name': operation.name + ' - ' + operation.workcenter_id.name,
                'uom_name': _("Minutes"),
                'quantity': duration_expected,
                'bom_cost': bom_cost,
                'currency_id': company.currency_id.id,
                'model': 'mrp.routing.workcenter',
                'availability_state': availability_state,
                'availability_delay': availability_delay,
                'availability_display': availability_display,
            })
            operation_index += 1
        return operations