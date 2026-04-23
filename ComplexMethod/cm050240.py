def _get_compatible_payment_methods(
        self, provider_ids, partner_id, currency_id=None, force_tokenization=False,
        is_express_checkout=False, report=None, **kwargs
    ):
        """ Search and return the payment methods matching the compatibility criteria.

        The compatibility criteria are that payment methods must: be supported by at least one of
        the providers; support the country of the partner if it exists; be primary payment methods
        (not a brand). If provided, the optional keyword arguments further refine the criteria.

        :param list provider_ids: The list of providers by which the payment methods must be at
                                  least partially supported to be considered compatible, as a list
                                  of `payment.provider` ids.
        :param int partner_id: The partner making the payment, as a `res.partner` id.
        :param int currency_id: The payment currency, if known beforehand, as a `res.currency` id.
        :param bool force_tokenization: Whether only payment methods supporting tokenization can be
                                        matched.
        :param bool is_express_checkout: Whether the payment is made through express checkout.
        :param dict report: The report in which each provider's availability status and reason must
                            be logged.
        :param dict kwargs: Optional data. This parameter is not used here.
        :return: The compatible payment methods.
        :rtype: payment.method
        """
        # Search compatible payment methods with the base domain.
        payment_methods = self.env['payment.method'].search([('is_primary', '=', True)])
        payment_utils.add_to_report(report, payment_methods)

        # Filter by compatible providers.
        unfiltered_pms = payment_methods
        payment_methods = payment_methods.filtered(
            lambda pm: any(p in provider_ids for p in pm.provider_ids.ids)
        )
        payment_utils.add_to_report(
            report,
            unfiltered_pms - payment_methods,
            available=False,
            reason=REPORT_REASONS_MAPPING['provider_not_available'],
        )

        # Handle the partner country; allow all countries if the list is empty.
        partner = self.env['res.partner'].browse(partner_id)
        if partner.country_id:  # The partner country must either not be set or be supported.
            unfiltered_pms = payment_methods
            payment_methods = payment_methods.filtered(
                lambda pm: (
                    not pm.supported_country_ids
                    or partner.country_id.id in pm.supported_country_ids.ids
                )
            )
            payment_utils.add_to_report(
                report,
                unfiltered_pms - payment_methods,
                available=False,
                reason=REPORT_REASONS_MAPPING['incompatible_country'],
            )

        # Handle the supported currencies; allow all currencies if the list is empty.
        if currency_id:
            unfiltered_pms = payment_methods
            payment_methods = payment_methods.filtered(
                lambda pm: (
                    not pm.supported_currency_ids
                    or currency_id in pm.supported_currency_ids.ids
                )
            )
            payment_utils.add_to_report(
                report,
                unfiltered_pms - payment_methods,
                available=False,
                reason=REPORT_REASONS_MAPPING['incompatible_currency'],
            )

        # Handle tokenization support requirements.
        if force_tokenization:
            unfiltered_pms = payment_methods
            payment_methods = payment_methods.filtered('support_tokenization')
            payment_utils.add_to_report(
                report,
                unfiltered_pms - payment_methods,
                available=False,
                reason=REPORT_REASONS_MAPPING['tokenization_not_supported'],
            )

        # Handle express checkout.
        if is_express_checkout:
            unfiltered_pms = payment_methods
            payment_methods = payment_methods.filtered('support_express_checkout')
            payment_utils.add_to_report(
                report,
                unfiltered_pms - payment_methods,
                available=False,
                reason=REPORT_REASONS_MAPPING['express_checkout_not_supported'],
            )

        return payment_methods