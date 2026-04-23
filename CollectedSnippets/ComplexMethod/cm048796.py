def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False, handle_price_include=True, include_caba_tags=False, rounding_method=None):
        """Compute all information required to apply taxes (in self + their children in case of a tax group).
        We consider the sequence of the parent for group of taxes.
        Eg. considering letters as taxes and alphabetic order as sequence::

            [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

        :param price_unit: The unit price of the line to compute taxes on.
        :param currency: The optional currency in which the price_unit is expressed.
        :param quantity: The optional quantity of the product to compute taxes on.
        :param product: The optional product to compute taxes on.
            Used to get the tags to apply on the lines.

        :param partner: The optional partner compute taxes on.
            Used to retrieve the lang to build strings and for potential extensions.

        :param is_refund: The optional boolean indicating if this is a refund.
        :param handle_price_include: Used when we need to ignore all tax included in price. If False, it means the
            amount passed to this method will be considered as the base of all computations.

        :param include_caba_tags: The optional boolean indicating if CABA tags need to be taken into account.
        :returns:
            ::

                {
                    'total_excluded': 0.0,    # Total without taxes
                    'total_included': 0.0,    # Total with taxes
                    'total_void'    : 0.0,    # Total with those taxes, that don't have an account set
                    'base_tags: : list<int>,  # Tags to apply on the base line
                    'taxes': [{               # One dict for each tax in self and their children
                        'id': int,
                        'name': str,
                        'amount': float,
                        'base': float,
                        'sequence': int,
                        'account_id': int,
                        'refund_account_id': int,
                        'analytic': bool,
                        'price_include': bool,
                        'tax_exigibility': str,
                        'tax_repartition_line_id': int,
                        'group': recordset,
                        'tag_ids': list<int>,
                        'tax_ids': list<int>,
                    }],
                }
        """
        if not self:
            company = self.env.company
        else:
            company = self[0].company_id._accessible_branches()[:1] or self[0].company_id

        # Compute tax details for a single line.
        currency = currency or company.currency_id
        if 'force_price_include' in self.env.context:
            special_mode = 'total_included' if self.env.context['force_price_include'] else 'total_excluded'
        elif not handle_price_include:
            special_mode = 'total_excluded'
        else:
            special_mode = False
        base_line = self._prepare_base_line_for_taxes_computation(
            None,
            partner_id=partner,
            currency_id=currency,
            product_id=product,
            tax_ids=self,
            price_unit=price_unit,
            quantity=quantity,
            is_refund=is_refund,
            special_mode=special_mode,
        )
        self._add_tax_details_in_base_line(base_line, company, rounding_method=rounding_method)
        self.with_context(
            compute_all_use_raw_base_lines=True,
        )._add_accounting_data_to_base_line_tax_details(base_line, company, include_caba_tags=include_caba_tags)

        tax_details = base_line['tax_details']
        total_void = total_excluded = tax_details['raw_total_excluded_currency']
        total_included = tax_details['raw_total_included_currency']

        # Convert to the 'old' compute_all api.
        taxes = []
        for tax_data in tax_details['taxes_data']:
            tax = tax_data['tax']
            for tax_rep_data in tax_data['tax_reps_data']:
                rep_line = tax_rep_data['tax_rep']
                taxes.append({
                    'id': tax.id,
                    'name': partner and tax.with_context(lang=partner.lang).name or tax.name,
                    'amount': tax_rep_data['tax_amount_currency'],
                    'base': tax_data['raw_base_amount_currency'],
                    'sequence': tax.sequence,
                    'account_id': tax_rep_data['account'].id,
                    'analytic': tax.analytic,
                    'use_in_tax_closing': rep_line.use_in_tax_closing,
                    'is_reverse_charge': tax_data['is_reverse_charge'],
                    'price_include': tax.price_include,
                    'tax_exigibility': tax.tax_exigibility,
                    'tax_repartition_line_id': rep_line.id,
                    'group': tax_data['group'],
                    'tag_ids': tax_rep_data['tax_tags'].ids,
                    'tax_ids': tax_rep_data['taxes'].ids,
                })
                if not rep_line.account_id:
                    total_void += tax_rep_data['tax_amount_currency']

        if self.env.context.get('round_base', True):
            total_excluded = currency.round(total_excluded)
            total_included = currency.round(total_included)

        return {
            'base_tags': base_line['tax_tag_ids'].ids,
            'taxes': taxes,
            'total_excluded': total_excluded,
            'total_included': total_included,
            'total_void': total_void,
        }