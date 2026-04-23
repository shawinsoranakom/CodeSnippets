def get_sales_section(line):
            move = line.move_id
            gst_treatment = move.l10n_in_gst_treatment
            transaction_type = get_transaction_type(move)
            line_tags = line.tax_tag_ids.ids
            is_inv = is_invoice(move)
            amt_limit = 100000 if not line.invoice_date or line.invoice_date >= date(2024, 11, 1) else 250000

            # ECO 9(5) Section: Check if the line has the ECO 9(5) tax tag
            if tags_have_categ(line_tags, ['eco_9_5']):
                return 'sale_eco_9_5'

            # Nil rated, Exempt, Non-GST Sales
            if gst_treatment != 'overseas':
                if any(tax.l10n_in_tax_type == 'nil_rated' for tax in line.tax_ids):
                    return 'sale_nil_rated'
                elif any(tax.l10n_in_tax_type == 'exempt' for tax in line.tax_ids):
                    return 'sale_exempt'
                elif any(tax.l10n_in_tax_type == 'non_gst' for tax in line.tax_ids):
                    return 'sale_non_gst_supplies'

            # B2CS: Unregistered or Consumer sales with gst tags
            if gst_treatment in ('unregistered', 'consumer') and not is_reverse_charge_tax(line):
                if (transaction_type == 'intra_state' and tags_have_categ(line_tags, ['sgst', 'cgst', 'cess'])) or (
                    transaction_type == "inter_state"
                    and tags_have_categ(line_tags, ['igst', 'cess'])
                    and not is_lut_tax(line)
                    and (
                        is_inv and move.amount_total <= amt_limit
                        or move.debit_origin_id and move.debit_origin_id.amount_total <= amt_limit
                        or move.reversed_entry_id and move.reversed_entry_id.amount_total <= amt_limit
                    )
                ):
                    return 'sale_b2cs'

            # If no relevant tags are found, or the tags do not match any category, mark as out of scope
            if not line_tags or not tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess', 'eco_9_5']):
                return 'sale_out_of_scope'

            # If it's a standard invoice (not a debit/credit note)
            if is_inv:
                # B2B with Reverse Charge and Regular
                if gst_treatment in ('regular', 'composition', 'uin_holders') and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess']) and not is_lut_tax(line):
                    if is_reverse_charge_tax(line):
                        return 'sale_b2b_rcm'
                    return 'sale_b2b_regular'

                if not is_reverse_charge_tax(line):
                    # B2CL: Unregistered interstate sales above threshold
                    if (
                        gst_treatment in ('unregistered', 'consumer')
                        and tags_have_categ(line_tags, ['igst', 'cess'])
                        and not is_lut_tax(line)
                        and transaction_type == 'inter_state'
                        and move.amount_total > amt_limit
                    ):
                        return 'sale_b2cl'
                    # Export with payment and without payment (under LUT) of tax
                    if gst_treatment == 'overseas' and tags_have_categ(line_tags, ['igst', 'cess']):
                        if is_lut_tax(line):
                            return 'sale_exp_wop'
                        return 'sale_exp_wp'
                    # SEZ with payment and without payment of tax
                    if gst_treatment == 'special_economic_zone' and tags_have_categ(line_tags, ['igst', 'cess']):
                        if is_lut_tax(line):
                            return 'sale_sez_wop'
                        return 'sale_sez_wp'
                    # Deemed export
                    if gst_treatment == 'deemed_export' and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess']) and not is_lut_tax(line):
                        return 'sale_deemed_export'

            # If it's not a standard invoice (i.e., it's a debit/credit note)
            if not is_inv:
                # CDN for B2B reverse charge and B2B regular
                if gst_treatment in ('regular', 'composition', 'uin_holders') and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess']) and not is_lut_tax(line):
                    if is_reverse_charge_tax(line):
                        return 'sale_cdnr_rcm'
                    return 'sale_cdnr_regular'
                if not is_reverse_charge_tax(line):
                    # CDN for SEZ exports with payment and without payment
                    if gst_treatment == 'special_economic_zone' and tags_have_categ(line_tags, ['igst', 'cess']):
                        if is_lut_tax(line):
                            return 'sale_cdnr_sez_wop'
                        return 'sale_cdnr_sez_wp'
                    # CDN for deemed exports
                    if gst_treatment == 'deemed_export' and tags_have_categ(line_tags, ['sgst', 'cgst', 'igst', 'cess']) and not is_lut_tax(line):
                        return 'sale_cdnr_deemed_export'
                    # CDN for B2CL (interstate > threshold)
                    if (
                        gst_treatment in ('unregistered', 'consumer')
                        and tags_have_categ(line_tags, ['igst', 'cess'])
                        and not is_lut_tax(line)
                        and transaction_type == 'inter_state'
                        and (
                            move.debit_origin_id and move.debit_origin_id.amount_total > amt_limit
                            or move.reversed_entry_id and move.reversed_entry_id.amount_total > amt_limit
                            or not move.reversed_entry_id and not move.is_inbound()
                        )
                    ):
                        return 'sale_cdnur_b2cl'
                    # CDN for exports with payment and without payment
                    if gst_treatment == 'overseas' and tags_have_categ(line_tags, ['igst', 'cess']):
                        if is_lut_tax(line):
                            return 'sale_cdnur_exp_wop'
                        return 'sale_cdnur_exp_wp'
            # If none of the above match, default to out of scope
            return 'sale_out_of_scope'