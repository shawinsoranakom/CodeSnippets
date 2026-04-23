def _get_computed_taxes(self):
        self.ensure_one()

        company_domain = self.env['account.tax']._check_company_domain(self.move_id.company_id)
        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            filtered_taxes_id = self.product_id.taxes_id.filtered_domain(company_domain)
            tax_ids = filtered_taxes_id or self.account_id.tax_ids.filtered(lambda tax: tax.type_tax_use == 'sale')

        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            filtered_supplier_taxes_id = self.product_id.supplier_taxes_id.filtered_domain(company_domain)
            tax_ids = filtered_supplier_taxes_id or self.account_id.tax_ids.filtered(lambda tax: tax.type_tax_use == 'purchase')

        elif self.env.context.get('account_default_taxes'):
            tax_ids = self.account_id.tax_ids

        else:
            tax_ids = False if self.env.context.get('skip_computed_taxes') or self.move_id.is_entry() else self.account_id.tax_ids

        if self.company_id and tax_ids:
            tax_ids = tax_ids._filter_taxes_by_company(self.company_id)

        if tax_ids and self.move_id.fiscal_position_id:
            tax_ids = self.move_id.fiscal_position_id.map_tax(tax_ids)

        return tax_ids