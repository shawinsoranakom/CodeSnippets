def get_section(line):
            tax_tags = line.tax_tag_ids.ids
            if any(tag == eco_9_5_tag for tag in tax_tags):
                return 'sale_eco_9_5'
            if any(tag in tax_tags for tag in all_gst_tags):
                return 'sale_b2cs'
            if any(tax.l10n_in_tax_type == 'nil_rated' for tax in line.tax_ids):
                return 'sale_nil_rated'
            if any(tax.l10n_in_tax_type == 'exempt' for tax in line.tax_ids):
                return 'sale_exempt'
            if any(tax.l10n_in_tax_type == 'non_gst' for tax in line.tax_ids):
                return 'sale_non_gst_supplies'
            return 'sale_out_of_scope'