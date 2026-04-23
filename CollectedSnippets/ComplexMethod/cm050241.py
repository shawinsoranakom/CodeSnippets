def _get_compatible_providers(
        self, company_id, partner_id, amount, currency_id=None, force_tokenization=False,
        is_express_checkout=False, is_validation=False, report=None, **kwargs
    ):
        """ Search and return the providers matching the compatibility criteria.

        The compatibility criteria are that providers must: not be disabled; be in the company that
        is provided; support the country of the partner if it exists; be compatible with the
        currency if provided. If provided, the optional keyword arguments further refine the
        criteria.

        :param int company_id: The company to which providers must belong, as a `res.company` id.
        :param int partner_id: The partner making the payment, as a `res.partner` id.
        :param float amount: The amount to pay. `0` for validation transactions.
        :param int currency_id: The payment currency, if known beforehand, as a `res.currency` id.
        :param bool force_tokenization: Whether only providers allowing tokenization can be matched.
        :param bool is_express_checkout: Whether the payment is made through express checkout.
        :param bool is_validation: Whether the operation is a validation.
        :param dict report: The report in which each provider's availability status and reason must
                            be logged.
        :param dict kwargs: Optional data. This parameter is not used here.
        :return: The compatible providers.
        :rtype: payment.provider
        """
        # Search compatible providers with the base domain.
        providers = self.env['payment.provider'].search([
            *self.env['payment.provider']._check_company_domain(company_id),
            ('state', 'in', ['enabled', 'test']),
        ])
        payment_utils.add_to_report(report, providers)

        # Filter by `is_published` state.
        if not self.env.user._is_internal():
            providers = providers.filtered('is_published')

        # Handle the partner country; allow all countries if the list is empty.
        partner = self.env['res.partner'].browse(partner_id)
        if partner.country_id:  # The partner country must either not be set or be supported.
            unfiltered_providers = providers
            providers = providers.filtered(
                lambda p: (
                    not p.available_country_ids
                    or partner.country_id.id in p.available_country_ids.ids
                )
            )
            payment_utils.add_to_report(
                report,
                unfiltered_providers - providers,
                available=False,
                reason=REPORT_REASONS_MAPPING['incompatible_country'],
            )

        # Handle the maximum amount.
        currency = self.env['res.currency'].browse(currency_id).exists()
        if not is_validation and currency:  # The currency is required to convert the amount.
            company = self.env['res.company'].browse(company_id).exists()
            date = fields.Date.context_today(self)
            converted_amount = currency._convert(amount, company.currency_id, company, date)
            unfiltered_providers = providers
            providers = providers.filtered(
                lambda p: (
                    not p.maximum_amount
                    or currency.compare_amounts(p.maximum_amount, converted_amount) != -1
                )
            )
            payment_utils.add_to_report(
                report,
                unfiltered_providers - providers,
                available=False,
                reason=REPORT_REASONS_MAPPING['exceed_max_amount'],
            )

        # Handle the available currencies; allow all currencies if the list is empty.
        if currency:
            unfiltered_providers = providers
            providers = providers.filtered(
                lambda p: (
                    not p.available_currency_ids
                    or currency.id in p.available_currency_ids.ids
                )
            )
            payment_utils.add_to_report(
                report,
                unfiltered_providers - providers,
                available=False,
                reason=REPORT_REASONS_MAPPING['incompatible_currency'],
            )

        # Handle tokenization support requirements.
        if force_tokenization or self._is_tokenization_required(**kwargs):
            unfiltered_providers = providers
            providers = providers.filtered('allow_tokenization')
            payment_utils.add_to_report(
                report,
                unfiltered_providers - providers,
                available=False,
                reason=REPORT_REASONS_MAPPING['tokenization_not_supported'],
            )

        # Handle express checkout.
        if is_express_checkout:
            unfiltered_providers = providers
            providers = providers.filtered('allow_express_checkout')
            payment_utils.add_to_report(
                report,
                unfiltered_providers - providers,
                available=False,
                reason=REPORT_REASONS_MAPPING['express_checkout_not_supported'],
            )

        return providers