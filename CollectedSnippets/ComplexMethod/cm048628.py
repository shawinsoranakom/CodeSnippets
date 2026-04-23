def name_search(self, name='', domain=None, operator='ilike', limit=100):
        move_type = self.env.context.get('move_type')
        if not move_type:
            return super().name_search(name, domain, operator, limit)

        partner = self.env.context.get('partner_id')
        suggested_accounts = self._order_accounts_by_frequency_for_partner(self.env.company.id, partner, move_type) if partner else []

        if not name and suggested_accounts:
            return [(record.id, record.display_name) for record in self.sudo().browse(suggested_accounts)]

        search_domain = Domain('display_name', 'ilike', name) if name else []
        move_type_accounts = {
            'out': ['income'],
            'in': ['expense', 'asset_fixed'],
        }
        allowed_account_types = move_type_accounts.get(move_type.split('_')[0])
        type_domain = [('account_type', 'in', allowed_account_types)] if allowed_account_types else []
        domain = Domain.AND([search_domain, type_domain, domain])

        records = self.with_context(preferred_account_ids=suggested_accounts).search_fetch(domain, ['display_name'], limit=limit)
        return [(record.id, record.display_name) for record in records]