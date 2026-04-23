def _compute_tax_totals(self):
        """ OVERRIDE

        For invoices based on ID company as of January 2025, there is a separate tax base computation for non-luxury goods.
        Tax base is supposed to be 11/12 of original while tax amount is increased from 11% to 12% hence effectively
        maintaining 11% tax amount.

        We change tax totals section to display adjusted base amount on invoice PDF for special non-luxury goods tax group.
        """
        super()._compute_tax_totals()
        for move in self.filtered(lambda m: m.is_sale_document()):
            # invoice might be coming from different companies, each tax group with unique XML ID
            non_luxury_tax_group = self.env['account.chart.template'].with_company(move.company_id.id).ref("l10n_id_tax_group_non_luxury_goods", raise_if_not_found=False)

            if not non_luxury_tax_group or move.invoice_date and move.invoice_date < fields.Date.to_date('2025-01-01'):
                continue

            # for every tax group component with non-luxury tax group, we adjust the base amount and adjust the display to
            # show base amount
            change_tax_base = False
            for subtotal in move.tax_totals["subtotals"]:
                for tax_group in subtotal["tax_groups"]:
                    if tax_group["id"] == non_luxury_tax_group.id:
                        tax_group.update({
                            "display_base_amount": tax_group["display_base_amount"] * (11 / 12),
                            "display_base_amount_currency": tax_group["display_base_amount_currency"] * (11 / 12),
                            "group_name": tax_group["group_name"] + " (on DPP)",
                        })
                        change_tax_base = True
            if change_tax_base:
                move.tax_totals["same_tax_base"] = False