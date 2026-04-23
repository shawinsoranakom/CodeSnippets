def _get_validation_currency(self):
        """ Return the currency to use for validation operations.

        The validation currency must be supported by both the provider and the payment method. If
        the payment method is not passed, only the provider's supported currencies are considered.
        If no suitable currency is found, the provider's company's currency is returned instead.

        For a provider to support tokenization and specify a different validation currency, it must
        override this method and return the appropriate validation currency.

        Note: `self.ensure_one()`

        :return: The validation currency.
        :rtype: recordset of `res.currency`
        """
        self.ensure_one()

        # Find the validation currency at the intersection of the provider's and payment method's
        # supported currencies. An empty recordset means that all currencies are supported.
        provider_currencies = self.available_currency_ids
        pm = self.env.context.get('validation_pm')
        pm_currencies = self.env['res.currency'] if not pm else pm.supported_currency_ids
        validation_currency = None
        if provider_currencies and pm_currencies:
            validation_currency = (provider_currencies & pm_currencies)[:1]
        elif provider_currencies and not pm_currencies:
            validation_currency = provider_currencies[:1]
        elif not provider_currencies and pm_currencies:
            validation_currency = pm_currencies[:1]
        if not validation_currency:  # All currencies are supported, or no suitable one was found.
            validation_currency = self.company_id.currency_id
        return validation_currency