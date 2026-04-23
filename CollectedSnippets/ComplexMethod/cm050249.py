def _validate_tax_groups(self):
        err_messages = []
        allowed_codes = {'01', '02', '03', '04', '05', '06', '09', '10'}
        must_be_zero_codes = {'07', '08'}

        for move in self:
            kode = move.l10n_id_kode_transaksi
            non_luxury_group = self.env['account.chart.template'].with_company(move.company_id.id).ref("l10n_id_tax_group_non_luxury_goods", raise_if_not_found=False)
            luxury_group = self.env['account.chart.template'].with_company(move.company_id.id).ref("l10n_id_tax_group_luxury_goods", raise_if_not_found=False)
            zero_group = self.env['account.chart.template'].with_company(move.company_id.id).ref("l10n_id_tax_group_0", raise_if_not_found=False)
            exempt_group = self.env['account.chart.template'].with_company(move.company_id.id).ref("l10n_id_tax_group_exempt", raise_if_not_found=False)
            stlg_group = self.env['account.chart.template'].with_company(move.company_id.id).ref("l10n_id_tax_group_stlg", raise_if_not_found=False)
            default_group = self.env['account.chart.template'].with_company(move.company_id.id).ref("default_tax_group", raise_if_not_found=False)
            product_lines = move.line_ids.filtered(lambda line: line.display_type == 'product')
            all_taxes = product_lines.mapped('tax_ids')
            tax_groups = set(all_taxes.mapped('tax_group_id'))
            ppn_groups = {non_luxury_group, luxury_group, zero_group, exempt_group, default_group}
            ppn_groups.discard(False)
            ppn_tax_groups = [g for g in tax_groups if g in ppn_groups]
            stlg_tax_groups = [g for g in tax_groups if g == stlg_group]

            # Multiple tax groups check
            if len(ppn_tax_groups) > 1:
                err_messages.append(_("Invoice %s: can only have one PPN tax group (excluding STLG).", move.name or ''))
            if len(stlg_tax_groups) > 1:
                err_messages.append(_("Invoice %s: can only have one STLG group.", move.name or ''))
            if not (ppn_tax_groups or stlg_tax_groups):
                err_messages.append(_("Invoice %s: need to have at least one PPN or STLG tax group.", move.name or ''))

            # Allowed codes (01-06, 09, 10)
            if kode in allowed_codes:
                for line in product_lines:
                    line_tax_groups = set(line.tax_ids.mapped('tax_group_id'))
                    if luxury_group and non_luxury_group and {luxury_group, non_luxury_group}.issubset(line_tax_groups):
                        err_messages.append(_(
                            "Invoice %(inv)s: line '%(line)s' contains both Luxury-Goods and Non-Luxury-Goods taxes.",
                            inv=move.name or '', line=line.product_id.display_name or '')
                        )
                    if non_luxury_group and stlg_group and {non_luxury_group, stlg_group}.issubset(line_tax_groups):
                        err_messages.append(_(
                            "Invoice %(inv)s: line '%(line)s' contains both Non-Luxury-Goods and STLG taxes.",
                            inv=move.name or '', line=line.product_id.display_name or '')
                        )
                    if stlg_group and stlg_group in line_tax_groups:
                        if not (luxury_group and luxury_group in line_tax_groups):
                            err_messages.append(_(
                                "Invoice %(inv)s: line '%(line)s' has STLG tax but missing the required Luxury-Goods tax.",
                                inv=move.name or '', line=line.product_id.display_name or '')
                            )
                    for tax in line.tax_ids:
                        if ((hasattr(tax, 'amount') and float(tax.amount) == 0.0) or (tax.tax_group_id in {zero_group, exempt_group})):
                            err_messages.append(_(
                                "Invoice %(inv)s: transaction code %(kode)s does not allow 0%% (Zero-rated or Exempt) taxes.",
                                inv=move.name or '', kode=kode)
                            )

            # Must-be-zero codes (07-08)
            elif kode in must_be_zero_codes:
                for line in product_lines:
                    for tax in line.tax_ids:
                        if hasattr(tax, 'amount') and float(tax.amount) != 0.0:
                            err_messages.append(_(
                                "Invoice %(inv)s: transaction code %(kode)s must always have tax amount 0%%.",
                                inv=move.name or '', kode=kode)
                            )
        return err_messages