def _include_pdf_specifics(self, doc, data=None):
        def get_color(decorator):
            return f"text-{decorator}" if decorator else ''

        if not data:
            data = {}
        footer_colspan = 2  # Name & Quantity
        doc['show_replenishments'] = data.get('replenishments') == '1'
        if doc['show_replenishments']:
            footer_colspan += 1
        doc['show_availabilities'] = data.get('availabilities') == '1'
        if doc['show_availabilities']:
            footer_colspan += 2  # Free to use / On Hand & Reserved
        doc['show_receipts'] = data.get('receipts') == '1'
        if doc['show_receipts']:
            footer_colspan += 1
        doc['show_unit_costs'] = data.get('unitCosts') == '1'
        if doc['show_unit_costs']:
            footer_colspan += 1
        doc['show_mo_costs'] = data.get('moCosts') == '1'
        doc['show_bom_costs'] = data.get('bomCosts') == '1'
        doc['show_real_costs'] = data.get('realCosts') == '1'
        doc['show_uom'] = self.env.user.has_group('uom.group_uom')
        if doc['show_uom']:
            footer_colspan += 1
        doc['data_mo_unit_cost'] = doc['summary'].get('mo_cost', 0) / (doc['summary'].get('quantity') or 1)
        doc['data_bom_unit_cost'] = doc['summary'].get('bom_cost', 0) / (doc['summary'].get('quantity') or 1)
        doc['data_real_unit_cost'] = doc['summary'].get('real_cost', 0) / (doc['summary'].get('quantity') or 1)
        doc['unfolded_ids'] = set(json.loads(data.get('unfoldedIds', '[]')))
        doc['footer_colspan'] = footer_colspan
        doc['get_color'] = get_color
        return doc