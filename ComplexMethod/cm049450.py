def l10n_in_grouping_key_generator(base_line, tax_data):
            invl = base_line['record']
            tax = tax_data['tax']
            if self.l10n_in_gst_treatment in ('overseas', 'special_economic_zone') and all(
                self.env.ref("l10n_in.tax_tag_igst") in rl.tag_ids
                for rl in tax.invoice_repartition_line_ids if rl.repartition_type == 'tax'
            ):
                tax_data['is_reverse_charge'] = False
            tag_ids = tax.invoice_repartition_line_ids.tag_ids.ids
            line_code = "other"
            xmlid_to_res_id = self.env['ir.model.data']._xmlid_to_res_id
            if not invl.currency_id.is_zero(tax_data['tax_amount_currency']):
                if xmlid_to_res_id("l10n_in.tax_tag_cess") in tag_ids:
                    if tax.amount_type != "percent":
                        line_code = "cess_non_advol"
                    else:
                        line_code = "cess"
                elif xmlid_to_res_id("l10n_in.tax_tag_state_cess") in tag_ids:
                    if tax.amount_type != "percent":
                        line_code = "state_cess_non_advol"
                    else:
                        line_code = "state_cess"
                else:
                    for gst in ["cgst", "sgst", "igst"]:
                        if xmlid_to_res_id("l10n_in.tax_tag_%s" % (gst)) in tag_ids:
                            # need to separate rc tax value so it's not pass to other values
                            line_code = f'{gst}_rc' if tax_data['is_reverse_charge'] else gst
            return {
                "tax": tax,
                "base_product_id": invl.product_id,
                "tax_product_id": invl.product_id,
                "base_product_uom_id": invl.product_uom_id,
                "tax_product_uom_id": invl.product_uom_id,
                "line_code": line_code,
            }