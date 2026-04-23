def _get_l10n_in_fiscal_tax_vals(self, fiscal_position_xml_ids):
        rates = [1, 2, 5, 12, 18, 28, 40]
        taxes_xml_ids = []

        if fiscal_position_xml_ids == 'fiscal_position_in_intra_state':
            taxes_xml_ids = [f"sgst_{tax_type}_{rate}" for tax_type in ["sale", "purchase"] for rate in rates]
        elif fiscal_position_xml_ids == 'fiscal_position_in_inter_state':
            taxes_xml_ids = [f"igst_{tax_type}_{rate}" for tax_type in ["sale", "purchase"] for rate in rates]
        elif fiscal_position_xml_ids == 'fiscal_position_in_export_sez_in':
            taxes_xml_ids = [f"igst_sale_{rate}_sez_exp" for rate in rates] + [f"igst_purchase_{rate}" for rate in rates] + ['igst_sale_0_sez_exp']
        elif fiscal_position_xml_ids == 'fiscal_position_in_lut_sez':
            taxes_xml_ids = [f"igst_sale_{rate}_sez_exp_lut" for rate in rates] + ['igst_sale_0_sez_exp_lut']
        elif fiscal_position_xml_ids == 'fiscal_position_in_lut_sez_1':
            taxes_xml_ids = [f"igst_sale_{rate}_sez_lut" for rate in rates] + ['igst_sale_0_sez_lut']
        return [Command.set(taxes_xml_ids)]