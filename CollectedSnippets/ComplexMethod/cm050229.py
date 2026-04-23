def _get_online_payment_error(self):
        """
        Returns the appropriate error message to be displayed if _has_to_be_paid() method returns False.
        """
        self.ensure_one()
        transactions = self.transaction_ids.filtered(lambda tx: tx.state in ('pending', 'authorized', 'done'))
        pending_transactions = transactions.filtered(
            lambda tx: tx.state in {'pending', 'authorized'}
                       and tx.provider_code not in {'none', 'custom'})
        enabled_feature = str2bool(
            self.env['ir.config_parameter'].sudo().get_param(
                'account_payment.enable_portal_payment'
            )
        )
        errors = []
        if not enabled_feature:
            errors.append(_("This invoice cannot be paid online."))
        if transactions or self.currency_id.is_zero(self.amount_residual):
            errors.append(_("There is no amount to be paid."))
        if self.state != 'posted':
            errors.append(_("This invoice isn't posted."))
        if self.currency_id.is_zero(self.amount_residual):
            errors.append(_("This invoice has already been paid."))
        if self.move_type != 'out_invoice':
            errors.append(_("This is not an outgoing invoice."))
        if pending_transactions:
            errors.append(_("There are pending transactions for this invoice."))
        return '\n'.join(errors)