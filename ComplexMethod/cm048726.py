def _compute_account_id(self):
        term_lines = self.filtered(lambda line: line.display_type == 'payment_term')
        if term_lines:
            moves = term_lines.move_id
            self.env.cr.execute("""
                WITH previous AS (
                    SELECT DISTINCT ON (line.move_id)
                           'account.move' AS model,
                           line.move_id AS id,
                           NULL AS account_type,
                           line.account_id AS account_id
                      FROM account_move_line line
                     WHERE line.move_id = ANY(%(move_ids)s)
                       AND line.display_type = 'payment_term'
                       AND line.id != ANY(%(current_ids)s)
                ),
                fallback AS (
                    SELECT DISTINCT ON (account_companies.res_company_id, account.account_type)
                           'res.company' AS model,
                           account_companies.res_company_id AS id,
                           account.account_type AS account_type,
                           account.id AS account_id
                      FROM account_account account
                      JOIN account_account_res_company_rel account_companies
                           ON account_companies.account_account_id = account.id
                     WHERE account_companies.res_company_id = ANY(%(company_ids)s)
                       AND account.account_type IN ('asset_receivable', 'liability_payable')
                       AND account.active = 't'
                )
                SELECT * FROM previous
                UNION ALL
                SELECT * FROM fallback
            """, {
                'company_ids': moves.company_id.ids,
                'move_ids': moves.ids,
                'partners': [f'res.partner,{pid}' for pid in moves.commercial_partner_id.ids],
                'current_ids': term_lines.ids
            })
            accounts = {
                (model, id, account_type): account_id
                for model, id, account_type, account_id in self.env.cr.fetchall()
            }
            for line in term_lines:
                account_type = 'asset_receivable' if line.move_id.is_sale_document(include_receipts=True) else 'liability_payable'
                move = line.move_id
                account_id = (
                    accounts.get(('account.move', move.id, None))
                    or move.with_company(move.company_id).commercial_partner_id['property_account_receivable_id' if account_type == 'asset_receivable' else 'property_account_payable_id'].id
                    or move.with_company(move.company_id).company_id.partner_id['property_account_receivable_id' if account_type == 'asset_receivable' else 'property_account_payable_id'].id
                    or accounts.get(('res.company', move.company_id.id, account_type))
                )
                if line.move_id.fiscal_position_id:
                    account_id = line.move_id.fiscal_position_id.map_account(self.env['account.account'].browse(account_id))
                line.account_id = account_id

        product_lines = self.filtered(lambda line: line.display_type == 'product' and line.move_id.is_invoice(True))
        for line in product_lines:
            if line.product_id:
                fiscal_position = line.move_id.fiscal_position_id
                accounts = line.with_company(line.company_id).product_id\
                    .product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                if line.move_id.is_sale_document(include_receipts=True):
                    line.account_id = accounts['income'] or line.account_id
                elif line.move_id.is_purchase_document(include_receipts=True):
                    line.account_id = accounts['expense'] or line.account_id
            elif line.partner_id:
                account_id = self.env['account.account']._get_most_frequent_account_for_partner(
                    company_id=line.company_id.id,
                    partner_id=line.partner_id.id,
                    move_type=line.move_id.move_type,
                )
                if account_id:
                    line.account_id = account_id
        for line in self:
            if not line.account_id and line.display_type not in ('line_section', 'line_subsection', 'line_note'):
                previous_two_accounts = line.move_id.line_ids.filtered(
                    lambda l: l.account_id and l.display_type == line.display_type
                )[-2:].account_id
                if len(previous_two_accounts) == 1 and len(line.move_id.line_ids) > 2:
                    line.account_id = previous_two_accounts
                else:
                    line.account_id = line.move_id.journal_id.default_account_id