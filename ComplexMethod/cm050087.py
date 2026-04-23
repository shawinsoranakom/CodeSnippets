def _ubl_add_line_item_commodity_classification_nodes(self, vals):
        item_node = vals['item_node']
        base_line = vals['line_vals']['base_line']
        product = base_line['product_id']
        nodes = item_node['cac:CommodityClassification'] = []

        if self.module_installed('account_intrastat'):
            intrastat_code = product.intrastat_code_id
            if intrastat_code.code:
                nodes.append(self._ubl_get_line_item_commodity_classification_node_from_intrastat_code(vals, intrastat_code))

        if self.module_installed('product_unspsc'):
            unspsc_code = product.unspsc_code_id
            if unspsc_code.code:
                nodes.append(self._ubl_get_line_item_commodity_classification_node_from_unspsc_code(vals, unspsc_code))

        if self.module_installed('l10n_ro_cpv_code'):
            cpv_code = product.cpv_code_id
            if cpv_code.code:
                nodes.append(self._ubl_get_line_item_commodity_classification_node_from_cpv_code(vals, cpv_code))

        if self.module_installed('l10n_hr_edi'):
            cg_code = base_line.get('cg_item_classification_code') or product.l10n_hr_kpd_category_id
            if cg_code.name:
                nodes.append(self._ubl_get_line_item_commodity_classification_node_from_cg_code(vals, cg_code))

        return nodes