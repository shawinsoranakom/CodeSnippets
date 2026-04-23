def _compute_tax_ids(self):
        for line in self:
            if line.display_type in ('line_section', 'line_subsection', 'line_note', 'payment_term') or line.is_imported:
                continue
            # /!\ Don't remove existing taxes if there is no explicit taxes set on the account.
            if line.product_id or (line.display_type != 'discount' and (line.account_id.tax_ids or not line.tax_ids)):
                line.tax_ids = line._get_computed_taxes()