def write(self, vals):
        # Handle payment methods being archived, detached from providers, or blocking tokenization.
        archiving = vals.get('active') is False
        detached_provider_ids = [
            v[0] for command, *v in vals['provider_ids'] if command == Command.UNLINK
        ] if 'provider_ids' in vals else []
        blocking_tokenization = vals.get('support_tokenization') is False
        if archiving or detached_provider_ids or blocking_tokenization:
            linked_tokens = self.env['payment.token'].with_context(active_test=True).search(
                Domain('payment_method_id', 'in', (self + self.brand_ids).ids)
                & (Domain('provider_id', 'in', detached_provider_ids) if detached_provider_ids else Domain.TRUE),
            )  # Fix `active_test` in the context forwarded by the view.
            linked_tokens.active = False

        # Prevent enabling a payment method if it is not linked to an enabled provider.
        if vals.get('active'):
            for pm in self:
                primary_pm = pm if pm.is_primary else pm.primary_payment_method_id
                if (
                    not primary_pm.active  # Don't bother for already enabled payment methods.
                    and all(p.state == 'disabled' for p in primary_pm.provider_ids)
                ):
                    raise UserError(_(
                        "This payment method needs a partner in crime; you should enable a payment"
                        " provider supporting this method first."
                    ))

        return super().write(vals)