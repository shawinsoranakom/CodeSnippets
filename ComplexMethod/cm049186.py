def _load_narration_translation(self):
        # Workaround to have the english/arabic version of the payment terms
        # in the report
        if not self:
            return
        moves_to_fix = self.env['account.move']
        for move in self.filtered(lambda m: m.narration and m.is_sale_document(include_receipts=True) and m.company_id.country_id and 'GCC' in m.company_id.country_id.country_group_codes):
            lang = move.partner_id.lang or self.env.user.lang
            if move.company_id.terms_type == 'html' or move.narration != move.company_id.with_context(lang=lang).invoice_terms:
                continue
            moves_to_fix |= move
        if not moves_to_fix:
            return
        self.env['res.company'].flush_model(['invoice_terms'])
        self.env.cr.execute('SELECT "id","invoice_terms" FROM "res_company" WHERE id = any(%s)', [moves_to_fix.company_id.ids])
        translation_by_company_id = {company_id: narration for company_id, narration in self.env.cr.fetchall()}
        self.env.cache.update_raw(moves_to_fix, self._fields['narration'], [
            translation_by_company_id[move.company_id.id]
            for move in moves_to_fix
        ], dirty=True)
        moves_to_fix.modified(['narration'])