def _get_tax_details(
        self,
        price_unit,
        quantity,
        precision_rounding=0.01,
        rounding_method='round_per_line',
        product=None,
        product_uom=None,
        special_mode=False,
        manual_tax_amounts=None,
        filter_tax_function=None,
    ):
        """ Compute the tax/base amounts for the current taxes.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param price_unit:          The price unit of the line.
        :param quantity:            The quantity of the line.
        :param precision_rounding:  The rounding precision for the 'round_per_line' method.
        :param rounding_method:     'round_per_line' or 'round_globally'.
        :param product:             The product of the line.
        :param product_uom:         The product uom of the line.
        :param special_mode:        Indicate a special mode for the taxes computation.
                            * total_excluded: The initial base of computation excludes all price-included taxes.
                            Suppose a tax of 21% price included. Giving 100 with special_mode = 'total_excluded'
                            will give you the same as 121 without any special_mode.
                            * total_included: The initial base of computation is the total with taxes.
                            Suppose a tax of 21% price excluded. Giving 121 with special_mode = 'total_included'
                            will give you the same as 100 without any special_mode.
                            Note: You can only expect accurate symmetrical taxes computation with not rounded price_unit
                            as input and 'round_globally' computation. Otherwise, it's not guaranteed.
        :param manual_tax_amounts:  TO BE REMOVED IN MASTER.
        :param filter_tax_function: Optional function to filter out some taxes from the computation.
        :return: A dict containing:
            'evaluation_context':       The evaluation_context parameter.
            'taxes_data':               A list of dictionaries, one per tax containing:
                'tax':                      The tax record.
                'base':                     The base amount of this tax.
                'tax_amount':               The tax amount of this tax.
            'total_excluded':           The total without tax.
            'total_included':           The total with tax.
        """
        def add_tax_amount_to_results(tax, tax_amount):
            taxes_data[tax.id]['tax_amount'] = tax_amount
            if rounding_method == 'round_per_line':
                taxes_data[tax.id]['tax_amount'] = float_round(taxes_data[tax.id]['tax_amount'], precision_rounding=precision_rounding)
            if tax.has_negative_factor:
                reverse_charge_taxes_data[tax.id]['tax_amount'] = -taxes_data[tax.id]['tax_amount']
            sorted_taxes._propagate_extra_taxes_base(tax, taxes_data, special_mode=special_mode)

        def eval_tax_amount(tax_amount_function, tax):
            is_already_computed = 'tax_amount' in taxes_data[tax.id]
            if is_already_computed:
                return

            tax_amount = tax_amount_function(
                taxes_data[tax.id]['batch'],
                raw_base + taxes_data[tax.id]['extra_base_for_tax'],
                evaluation_context,
            )
            if tax_amount is not None:
                add_tax_amount_to_results(tax, tax_amount)

        def prepare_tax_extra_data(tax, **kwargs):
            if tax.has_negative_factor:
                price_include = False
            elif special_mode == 'total_included':
                price_include = True
            elif special_mode == 'total_excluded':
                price_include = False
            else:
                price_include = tax.price_include
            return {
                **kwargs,
                'tax': tax,
                'price_include': price_include,
                'extra_base_for_tax': 0.0,
                'extra_base_for_base': 0.0,
            }

        # Flatten the taxes, order them and filter them if necessary.
        batching_results = self._batch_for_taxes_computation(special_mode=special_mode, filter_tax_function=filter_tax_function)
        sorted_taxes = batching_results['sorted_taxes']
        taxes_data = {}
        reverse_charge_taxes_data = {}
        for tax in sorted_taxes:
            taxes_data[tax.id] = prepare_tax_extra_data(
                tax,
                group=batching_results['group_per_tax'].get(tax.id),
                batch=batching_results['batch_per_tax'][tax.id],
            )
            if tax.has_negative_factor:
                reverse_charge_taxes_data[tax.id] = {
                    **taxes_data[tax.id],
                    'is_reverse_charge': True,
                }

        raw_base = quantity * price_unit
        if rounding_method == 'round_per_line':
            raw_base = float_round(raw_base, precision_rounding=precision_rounding)

        evaluation_context = {
            'product': sorted_taxes._eval_taxes_computation_turn_to_product_values(product=product),
            'uom': sorted_taxes._eval_taxes_computation_turn_to_product_uom_values(product_uom=product_uom),
            'price_unit': price_unit,
            'quantity': quantity,
            'raw_base': raw_base,
            'special_mode': special_mode,
        }

        # Define the order in which the taxes must be evaluated.
        # Fixed taxes are computed directly because they could affect the base of a price included batch right after.
        # Suppose:
        # t1: fixed tax of 1, include base amount
        # t2: 21% price included tax
        # If the price unit is 121, the base amount of t1 is computed as 121 / 1.1 = 110
        # With special_mode = 'total_excluded', 110 is provided as price unit.
        # To compute the base amount of t2, we need to add back the tax amount of t1.
        for tax in reversed(sorted_taxes):
            eval_tax_amount(tax._eval_tax_amount_fixed_amount, tax)

        # Then, let's travel the batches in the reverse order and process the price-included taxes.
        for tax in reversed(sorted_taxes):
            if taxes_data[tax.id]['price_include']:
                eval_tax_amount(tax._eval_tax_amount_price_included, tax)

        # Then, let's travel the batches in the normal order and process the price-excluded taxes.
        for tax in sorted_taxes:
            if not taxes_data[tax.id]['price_include']:
                eval_tax_amount(tax._eval_tax_amount_price_excluded, tax)

        # Mark the base to be computed in the descending order. The order doesn't matter for no special mode or 'total_excluded' but
        # it must be in the reverse order when special_mode is 'total_included'.
        subsequent_taxes = self.env['account.tax']
        for tax in reversed(sorted_taxes):
            tax_data = taxes_data[tax.id]
            if 'tax_amount' not in tax_data:
                continue

            # Base amount.
            tax_id_str = str(tax.id)
            total_tax_amount = sum(taxes_data[other_tax.id]['tax_amount'] for other_tax in tax_data['batch'])
            total_tax_amount += sum(
                reverse_charge_taxes_data[other_tax.id]['tax_amount']
                for other_tax in taxes_data[tax.id]['batch']
                if other_tax.has_negative_factor
            )
            base = raw_base + tax_data['extra_base_for_base']
            if tax_data['price_include'] and special_mode in (False, 'total_included'):
                base -= total_tax_amount
            tax_data['base'] = base

            # Subsequent taxes.
            tax_data['taxes'] = self.env['account.tax']
            if tax.include_base_amount:
                tax_data['taxes'] |= subsequent_taxes

            # Reverse charge.
            if tax.has_negative_factor:
                reverse_charge_tax_data = reverse_charge_taxes_data[tax.id]
                reverse_charge_tax_data['base'] = base
                reverse_charge_tax_data['taxes'] = tax_data['taxes']

            if tax.is_base_affected:
                subsequent_taxes |= tax

        taxes_data_list = []
        for tax_data in taxes_data.values():
            if 'tax_amount' in tax_data:
                taxes_data_list.append(tax_data)
                tax = tax_data['tax']
                if tax.has_negative_factor:
                    taxes_data_list.append(reverse_charge_taxes_data[tax.id])

        if taxes_data_list:
            total_excluded = taxes_data_list[0]['base']
            tax_amount = sum(tax_data['tax_amount'] for tax_data in taxes_data_list)
            total_included = total_excluded + tax_amount
        else:
            total_included = total_excluded = raw_base

        return {
            'total_excluded': total_excluded,
            'total_included': total_included,
            'taxes_data': [
                {
                    'tax': tax_data['tax'],
                    'taxes': tax_data['taxes'],
                    'group': batching_results['group_per_tax'].get(tax_data['tax'].id) or self.env['account.tax'],
                    'batch': batching_results['batch_per_tax'][tax_data['tax'].id],
                    'tax_amount': tax_data['tax_amount'],
                    'price_include': tax_data['price_include'],
                    'base_amount': tax_data['base'],
                    'is_reverse_charge': tax_data.get('is_reverse_charge', False),
                }
                for tax_data in taxes_data_list
            ],
        }