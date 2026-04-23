def get_purchase_section(line):
            move = line.move_id
            gst_treatment = move.l10n_in_gst_treatment
            line_tags = line.tax_tag_ids.ids
            is_bill = is_move_bill(move)

            # Nil rated, Exempt, Non-GST purchases
            if gst_treatment != 'overseas':
                if any(tax.l10n_in_tax_type == 'nil_rated' for tax in line.tax_ids):
                    return 'purchase_nil_rated'
                elif any(tax.l10n_in_tax_type == 'exempt' for tax in line.tax_ids):
                    return 'purchase_exempt'
                elif any(tax.l10n_in_tax_type == 'non_gst' for tax in line.tax_ids):
                    return 'purchase_non_gst_supplies'

            # If no relevant tags are found, or the tags do not match any category, mark as out of scope
            if not line_tags or not tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess']):
                return 'purchase_out_of_scope'

            if is_bill:
                # B2B Regular and Reverse Charge purchases
                if (gst_treatment in ('regular', 'composition', 'uin_holders') and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess'])):
                    if is_reverse_charge_tax(line):
                        return 'purchase_b2b_rcm'
                    return 'purchase_b2b_regular'

                if not is_reverse_charge_tax(line) and (
                    gst_treatment == 'deemed_export' and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess'])
                    or gst_treatment == 'special_economic_zone' and tags_have_categ(line_tags, ['igst', 'cess'])
                ):
                    return 'purchase_b2b_regular'

                # B2C Unregistered or Consumer sales with gst tags
                if gst_treatment in ('unregistered', 'consumer') and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess']) and is_reverse_charge_tax(line):
                    return 'purchase_b2c_rcm'

                # export service type products purchases
                if gst_treatment == 'overseas' and any(tax.tax_scope == 'service' for tax in line.tax_ids | line.tax_line_id) and tags_have_categ(line_tags, ['igst', 'cess']):
                    return 'purchase_imp_services'

                # export goods type products purchases
                if gst_treatment == 'overseas' and tags_have_categ(line_tags, ['igst', 'cess']) and not is_reverse_charge_tax(line):
                    return 'purchase_imp_goods'

            if not is_bill:
                # credit notes for b2b purchases
                if gst_treatment in ('regular', 'composition', 'uin_holders') and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess']):
                    if is_reverse_charge_tax(line):
                        return 'purchase_cdnr_rcm'
                    return 'purchase_cdnr_regular'

                # credit notes for b2c purchases
                if gst_treatment in ('unregistered', 'consumer') and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess']) and is_reverse_charge_tax(line):
                    return 'purchase_cdnur_rcm'

                if not is_reverse_charge_tax(line):
                    if gst_treatment == 'deemed_export' and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess'])\
                        or gst_treatment == 'special_economic_zone' and tags_have_categ(line_tags, ['igst', 'cess']):
                        return 'purchase_cdnr_regular'

                    if gst_treatment == 'overseas' and tags_have_categ(line_tags, ['igst', 'cess']):
                        return 'purchase_cdnur_regular'

            # If none of the above match, default to out of scope
            return 'purchase_out_of_scope'