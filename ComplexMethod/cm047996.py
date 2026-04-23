def _build_spreadsheet_formula_domain(self, formula_params, default_accounts=False):
        company_id = formula_params.get("company_id") or self.env.company.id
        company = self.env["res.company"].browse(company_id)
        start, end = self._get_date_period_boundaries(formula_params["date_range"], company)

        balance_domain = Domain([
            ("account_id.include_initial_balance", "=", True),
            ("date", "<=", end),
        ])
        pnl_domain = Domain([
            ("account_id.include_initial_balance", "=", False),
            ("date", ">=", start),
            ("date", "<=", end),
        ])
        period_domain = balance_domain | pnl_domain

        # Determine account domain based on tags or codes
        if 'account_tag_ids' in formula_params:
            tag_ids = [int(tag_id) for tag_id in formula_params["account_tag_ids"]]
            account_id_domain = Domain('account_id.tag_ids', 'in', tag_ids) if tag_ids else Domain.FALSE
        elif 'codes' in formula_params:
            codes = [code for code in formula_params.get("codes", []) if code]
            default_domain = Domain.FALSE
            if not codes:
                if not default_accounts:
                    return default_domain
                default_domain = Domain('account_type', 'in', ['liability_payable', 'asset_receivable'])

            # It is more optimized to (like) search for code directly in account.account than in account_move_line
            code_domain = Domain.OR(
                Domain("code", "=like", f"{code}%")
                for code in codes
            )
            account_domain = code_domain | default_domain
            account_ids = self.env["account.account"].with_company(company_id).search(account_domain).ids
            account_id_domain = [("account_id", "in", account_ids)]
        else:
            account_id_domain = Domain.FALSE

        posted_domain = [("move_id.state", "!=", "cancel")] if formula_params.get("include_unposted") else [("move_id.state", "=", "posted")]

        domain = Domain.AND([account_id_domain, period_domain, [("company_id", "=", company_id)], posted_domain])

        partner_ids = [int(partner_id) for partner_id in formula_params.get('partner_ids', []) if partner_id]
        if partner_ids:
            domain &= Domain("partner_id", "in", partner_ids)

        return domain