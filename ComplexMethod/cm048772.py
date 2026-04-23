def _prepare_base_line_for_taxes_computation(self, record, **kwargs):
        """ Convert any representation of a business object ('record') into a base line being a python
        dictionary that will be used to use the generic helpers for the taxes computation.

        The whole method is designed to ease the conversion from a business record.
        For example, when passing either account.move.line, either sale.order.line or purchase.order.line,
        providing explicitely a 'product_id' in kwargs is not necessary since all those records already have
        an `product_id` field.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param record:  A representation of a business object a.k.a a record or a dictionary.
        :param kwargs:  The extra values to override some values that will be taken from the record.
        :return:        A dictionary representing a base line.
        """
        def load(field, fallback):
            return self._get_base_line_field_value_from_record(record, field, kwargs, fallback)

        currency = (
            load('currency_id', None)
            or load('company_currency_id', None)
            or load('company_id', self.env['res.company']).currency_id
            or self.env['res.currency']
        )

        base_line = {
            **kwargs,
            'record': record,
            'id': load('id', 0),

            # Basic fields:
            'product_id': load('product_id', self.env['product.product']),
            'product_uom_id': load('product_uom_id', self.env['uom.uom']),
            'tax_ids': load('tax_ids', self.env['account.tax']),
            'price_unit': load('price_unit', 0.0),
            'quantity': load('quantity', 0.0),
            'discount': load('discount', 0.0),
            'currency_id': currency,

            # The special_mode for the taxes computation:
            # - False for the normal behavior.
            # - total_included to force all taxes to be price included.
            # - total_excluded to force all taxes to be price excluded.
            'special_mode': kwargs.get('special_mode') or False,

            # A special typing of base line for some custom behavior:
            # - False for the normal behavior.
            # - early_payment if the base line represent an early payment in mixed mode.
            # - cash_rounding if the base line is a delta to round the business object for the cash rounding feature.
            # - non_deductible if the base line is used to compute non deductible amounts in bills.
            'special_type': kwargs.get('special_type') or False,

            # All computation are managing the foreign currency and the local one.
            # This is the rate to be applied when generating the tax details (see '_add_tax_details_in_base_line').
            'rate': load('rate', 1.0),

            # Add a function allowing to filter out some taxes during the evaluation. Those taxes can't be removed from the base_line
            # when dealing with group of taxes to maintain a correct link between the child tax and its parent.
            'filter_tax_function': kwargs.get('filter_tax_function') or None,

            # ===== Accounting stuff =====

            # The sign of the business object regarding its accounting balance.
            'sign': load('sign', 1.0),

            # If the document is a refund or not to know which repartition lines must be used.
            'is_refund': load('is_refund', False),

            # Extra fields for tax lines generation:
            'partner_id': load('partner_id', self.env['res.partner']),
            'account_id': load('account_id', self.env['account.account']),
            'analytic_distribution': load('analytic_distribution', None),
        }

        extra_tax_data = self._import_base_line_extra_tax_data(base_line, load('extra_tax_data', {}) or {})
        base_line.update({
            # Allow to split the computation of taxes on subset of lines. For example with a down payment of 300 on a sale order of 1000,
            # the last invoice will have an amount of 1000 - 300 = 700. However, the taxes should be computed in 2 subsets of lines:
            # - the original lines for a total of 1000.0
            # - the previous down payment lines for a total of -300.0
            'computation_key': kwargs.get('computation_key') or extra_tax_data.get('computation_key'),

            # For all computation that are inferring a base amount in order to reach a total you know in advance, you have to force some
            # base/tax amounts for the computation (E.g. down payment, combo products, global discounts etc).
            'manual_total_excluded_currency': kwargs.get('manual_total_excluded_currency') or extra_tax_data.get('manual_total_excluded_currency'),
            'manual_total_excluded': kwargs.get('manual_total_excluded') or extra_tax_data.get('manual_total_excluded'),
            'manual_tax_amounts': kwargs.get('manual_tax_amounts') or extra_tax_data.get('manual_tax_amounts'),
        })
        if 'price_unit' in extra_tax_data:
            base_line['price_unit'] = extra_tax_data['price_unit']

        # Propagate custom values.
        if record and isinstance(record, dict):
            for k, v in record.items():
                if k.startswith('_') and k not in base_line:
                    base_line[k] = v

        return base_line