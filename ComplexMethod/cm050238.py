def _onchange_warn_before_disabling_tokens(self):
        """ Display a warning about the consequences of archiving the payment method, detaching it
        from a provider, or removing its support for tokenization.

        Let the user know that the related tokens will be archived.

        :return: A client action with the warning message, if any.
        :rtype: dict
        """
        disabling = self._origin.active and not self.active
        detached_providers = self._origin.provider_ids.filtered(
            lambda p: p.id not in self.provider_ids.ids
        )  # Cannot use recordset difference operation because self.provider_ids is a set of NewIds.
        blocking_tokenization = self._origin.support_tokenization and not self.support_tokenization
        if disabling or detached_providers or blocking_tokenization:
            related_tokens = self.env['payment.token'].with_context(active_test=True).search(
                Domain('payment_method_id', 'in', (self._origin + self._origin.brand_ids).ids)
                & (Domain('provider_id', 'in', detached_providers.ids) if detached_providers else Domain.TRUE),
            )  # Fix `active_test` in the context forwarded by the view.
            if related_tokens:
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "This action will also archive %s tokens that are registered with this "
                            "payment method.", len(related_tokens)
                        )
                    }
                }