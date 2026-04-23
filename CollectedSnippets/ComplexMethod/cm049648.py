def _post(self, soft=True):
        for move in self:
            if move.country_code == 'HR' and move.is_sale_document():
                if not move.l10n_hr_fiscal_user_id:
                    move.l10n_hr_fiscal_user_id = move.env.user.partner_id
            if move.l10n_hr_mer_document_eid and move.is_purchase_document():
                if move.l10n_hr_business_document_status == '1':
                    raise UserError(self.env._("This vendor bill is already rejected according to the Tax Authority."))
                elif move.l10n_hr_business_document_status in ('4', '99'):
                    _mer_api_update_document_process_status(
                        move.company_id,
                        move.l10n_hr_mer_document_eid,
                        0,
                    )
                    move.l10n_hr_edi_addendum_id.business_document_status = '0'
                    _logger.info("Document eID %s reported as approved by recepient.", move.l10n_hr_mer_document_eid)
        return super()._post(soft=soft)