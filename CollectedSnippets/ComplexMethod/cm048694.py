def _except_audit_trail(self):
        audit_trail_attachments = self.filtered(lambda attachment:
            attachment.res_model == 'account.move'
            and attachment.res_id
            and attachment.raw
            and attachment.company_id.restrictive_audit_trail
            and guess_mimetype(attachment.raw) in (
                'application/pdf',
                'application/xml',
            )
        )
        id2move = self.env['account.move'].browse(set(audit_trail_attachments.mapped('res_id'))).exists().grouped('id')
        for attachment in audit_trail_attachments:
            move = id2move.get(attachment.res_id)
            if move and move.posted_before and move.company_id.restrictive_audit_trail:
                ue = UserError(_("You cannot remove parts of a restricted audit trail."))
                ue._audit_trail = True
                raise ue