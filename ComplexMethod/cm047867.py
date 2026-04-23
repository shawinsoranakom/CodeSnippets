def _simulate_bom_planning(self, bom, product, start_date, quantity, simulated_leaves_per_workcenter=False):
        """ Simulate planning of all the operations depending on the workcenters work schedule.
        (see '_plan_workorders' & '_link_workorders_and_moves')
        """
        bom.ensure_one()
        if not bom.operation_ids:
            return {}
        if not product:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
        planning_per_operation = {}
        if simulated_leaves_per_workcenter is False:
            simulated_leaves_per_workcenter = defaultdict(list)
        if bom.allow_operation_dependencies:
            final_operations = bom.operation_ids.filtered(lambda o: not o.needed_by_operation_ids)
            for operation in final_operations:
                if operation._skip_operation_line(product):
                    continue
                self._simulate_operation_planning(operation, product, start_date, quantity, planning_per_operation, simulated_leaves_per_workcenter)
        else:
            for operation in bom.operation_ids:
                if operation._skip_operation_line(product):
                    continue
                self._simulate_operation_planning(operation, product, start_date, quantity, planning_per_operation, simulated_leaves_per_workcenter)
                start_date = planning_per_operation[operation]['date_finished']
        return planning_per_operation