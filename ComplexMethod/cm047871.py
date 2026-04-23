def _get_report_extra_lines(self, summary, components, operations, production):
        currency = summary.get('currency', self.env.company.currency_id)
        unit_mo_cost = currency.round(summary.get('mo_cost', 0) / (summary.get('quantity') or 1))
        unit_bom_cost = currency.round(summary.get('bom_cost', 0) / (summary.get('quantity') or 1))
        unit_real_cost = currency.round(summary.get('real_cost', 0) / (summary.get('quantity') or 1))
        extras = {
            'unit_mo_cost': unit_mo_cost,
            'unit_bom_cost': unit_bom_cost,
            'unit_real_cost': unit_real_cost,
        }
        if production.state == 'done':
            production_qty = summary.get('quantity') or 1.0
            extras['total_mo_cost_components'] = sum(compo.get('summary', {}).get('mo_cost', 0.0) for compo in components)
            extras['total_bom_cost_components'] = sum(compo.get('summary', {}).get('bom_cost', 0.0) for compo in components)
            extras['total_real_cost_components'] = sum(compo.get('summary', {}).get('real_cost', 0.0) for compo in components)
            extras['unit_mo_cost_components'] = extras['total_mo_cost_components'] / production_qty
            extras['unit_bom_cost_components'] = extras['total_bom_cost_components'] / production_qty
            extras['unit_real_cost_components'] = extras['total_real_cost_components'] / production_qty
            extras['total_mo_cost_operations'] = operations.get('summary', {}).get('mo_cost', 0.0)
            extras['total_bom_cost_operations'] = operations.get('summary', {}).get('bom_cost', 0.0)
            extras['total_real_cost_operations'] = operations.get('summary', {}).get('real_cost', 0.0)
            extras['unit_mo_cost_operations'] = extras['total_mo_cost_operations'] / production_qty
            extras['unit_bom_cost_operations'] = extras['total_bom_cost_operations'] / production_qty
            extras['unit_real_cost_operations'] = extras['total_real_cost_operations'] / production_qty
            extras['total_mo_cost'] = extras['total_mo_cost_components'] + extras['total_mo_cost_operations']
            extras['total_bom_cost'] = extras['total_bom_cost_components'] + extras['total_bom_cost_operations']
            extras['total_real_cost'] = extras['total_real_cost_components'] + extras['total_real_cost_operations']
        return extras