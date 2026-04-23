def _get_operations_data(self, production, level=0, current_index=False):
        if production.state == "done":
            return self._get_finished_operation_data(production, level, current_index)
        currency = (production.company_id or self.env.company).currency_id
        operation_uom = _("Minutes")
        operations = []
        total_expected_time = 0.0
        total_current_time = 0.0
        total_bom_cost = False
        total_expected_cost = 0.0
        total_real_cost = 0.0
        for index, workorder in enumerate(production.workorder_ids):
            estimate_cost = workorder._should_estimate_cost()
            wo_duration = workorder.duration_expected if estimate_cost else workorder.get_duration()
            mo_cost = workorder._compute_expected_operation_cost()
            bom_cost = self._get_bom_operation_cost(workorder, production, kit_operation=self._get_kit_operations(production.bom_id))
            real_cost = mo_cost if estimate_cost else workorder._compute_current_operation_cost()
            real_cost_decorator = False
            mo_cost_decorator = False
            if self._is_production_started(production):
                mo_cost = mo_cost if workorder.duration_expected else workorder._get_current_theorical_operation_cost()
                real_cost_decorator = self._get_comparison_decorator(mo_cost, real_cost, 0.01)
            elif production.state == "confirmed":
                if workorder.operation_id not in production.bom_id.operation_ids:
                    bom_cost = 0
                mo_cost_decorator = self._get_comparison_decorator(bom_cost, mo_cost, 0.01)
            else:
                if not production.bom_id:
                    bom_cost = mo_cost
                mo_cost_decorator = 'danger' if isinstance(bom_cost, bool) and not bom_cost else self._get_comparison_decorator(bom_cost, mo_cost, 0.01)
            is_workorder_started = not float_is_zero(wo_duration, precision_digits=2)

            operations.append({
                'level': level,
                'index': f"{current_index}W{index}",
                'model': workorder._name,
                'id': workorder.id,
                'name': workorder.name,
                'state': workorder.state,
                'formatted_state': self._format_state(workorder),
                'quantity': workorder.duration_expected if float_is_zero(wo_duration, precision_digits=2) else wo_duration,
                'uom_name': operation_uom,
                'production_id': production.id,
                'unit_cost': mo_cost / (workorder.duration_expected or 1),
                'mo_cost': mo_cost,
                'mo_cost_decorator': mo_cost_decorator,
                'bom_cost': bom_cost,
                'real_cost': real_cost,
                'real_cost_decorator': real_cost_decorator,
                'currency_id': currency.id,
                'currency': currency,
            })
            total_expected_time += workorder.duration_expected
            total_current_time += wo_duration if is_workorder_started else workorder.duration_expected
            total_expected_cost += production.company_id.currency_id.round(mo_cost)
            total_bom_cost = self._sum_bom_cost(total_bom_cost, bom_cost)
            total_real_cost += real_cost

        mo_cost_decorator = False
        if not self._is_production_started(production):
            mo_cost_decorator = self._get_comparison_decorator(total_bom_cost or 0.0, total_expected_cost, 0.01)

        return {
            'summary': {
                'index': f"{current_index}W",
                'quantity': total_current_time,
                'mo_cost': total_expected_cost,
                'mo_cost_decorator': mo_cost_decorator,
                'bom_cost': total_bom_cost,
                'real_cost': total_real_cost,
                'real_cost_decorator': self._get_comparison_decorator(total_expected_cost, total_real_cost, 0.01) if self._is_production_started(production) else False,
                'uom_name': operation_uom,
                'currency_id': currency.id,
                'currency': currency,
            },
            'details': operations,
        }