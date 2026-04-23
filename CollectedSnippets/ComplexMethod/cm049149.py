def action_pos_order_paid(self):
        res = super().action_pos_order_paid()

        if self.l10n_es_tbai_is_required and not self.to_invoice:
            error = self._l10n_es_tbai_post()

            if error:
                chain_head_doc = self.company_id._get_l10n_es_tbai_last_chained_document()
                chain_head_order = self.search([('l10n_es_tbai_post_document_id', '=', chain_head_doc.id)])

                if chain_head_doc and chain_head_order and chain_head_order != self and chain_head_doc.state != 'accepted':
                    chain_head_order._l10n_es_tbai_post()
                    if self.env['account.move.send']._can_commit():
                        self.env.cr.commit()
                    self._l10n_es_tbai_post()

        return res