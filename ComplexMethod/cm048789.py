def _dispatch_return_of_merchandise_lines(self, base_lines, company):
        """ Dispatch the return of merchandise lines present inside the base_lines passed as parameter across the others under the
        'return_of_merchandise_base_lines' key.
        What we call a return of merchandise is when the negative line matches exactly the parent line but has a negative quantity.
        So if you have 2 base lines, one with a quantity of 3 and the other with a quantity of -1, this method tries to reduce the
        quantity instead of considering the negative lines as a discount.

        [!] Only added python-side.

        :param base_lines:  A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:     The company owning the base lines.
        :return:            New base lines without any return of merchandise but sub-lines added under the 'return_of_merchandise_base_lines' key.
        """
        new_base_lines = []
        mapping = defaultdict(lambda: {
            '+': [],
            '-': [],
        })
        dispatched_neg_base_lines = []
        for base_line in base_lines:
            new_base_line = {
                **base_line,
                'return_of_merchandise_base_lines': [],
            }
            new_base_lines.append(new_base_line)

            if not base_line['product_id'] or base_line['quantity'] == 0.0:
                continue

            key = frozendict({
                'tax_ids': base_line['tax_ids'].ids,
                'product': base_line['product_id'].id,
                'price_unit': base_line['price_unit'],
                'discount': base_line['discount'],
            })

            is_negative = base_line['tax_details']['raw_total_excluded_currency'] < 0.0
            mapping[key]['-' if is_negative else '+'].append(new_base_line)

        for signed_base_lines in mapping.values():
            plus_base_lines = sorted(signed_base_lines['+'], key=lambda base_line: -base_line['quantity'])
            iter_plus_base_lines = iter(plus_base_lines)
            neg_base_lines = sorted(signed_base_lines['-'], key=lambda base_line: base_line['quantity'])
            iter_neg_base_lines = iter(neg_base_lines)
            plus_base_line = None
            plus_base_line_quantity = None
            neg_base_line = None
            neg_base_line_quantity = None
            target_factors_per_neg_base_line = []
            target_factors = None
            while True:

                if not neg_base_line or not neg_base_line_quantity:
                    neg_base_line = next(iter_neg_base_lines, None)
                    if neg_base_line:
                        neg_base_line_quantity = abs(neg_base_line['quantity'])
                        target_factors = []
                        target_factors_per_neg_base_line.append(target_factors)
                    else:
                        break

                if not plus_base_line or not plus_base_line_quantity:
                    plus_base_line = next(iter_plus_base_lines, None)
                    if plus_base_line:
                        plus_base_line_quantity = abs(plus_base_line['quantity'])
                    else:
                        break

                quantity_to_dispatch = min(neg_base_line_quantity, plus_base_line_quantity)
                target_factors.append({
                    'factor': quantity_to_dispatch / abs(neg_base_line['quantity']),
                    'quantity_to_dispatch': quantity_to_dispatch,
                    'plus_base_line': plus_base_line,
                    'quantity': -quantity_to_dispatch,
                })
                plus_base_line_quantity -= quantity_to_dispatch
                neg_base_line_quantity -= quantity_to_dispatch

            def populate_function(base_line, target_factor, kwargs):
                kwargs['price_unit'] = base_line['price_unit']
                kwargs['quantity'] = -target_factor['quantity_to_dispatch']

            for target_factors, neg_base_line in zip(target_factors_per_neg_base_line, neg_base_lines):
                if not target_factors:
                    continue

                dispatched_neg_base_lines.append(neg_base_line)
                splitted_base_lines = self._split_base_line(
                    base_line=neg_base_line,
                    company=company,
                    target_factors=target_factors,
                    populate_function=populate_function,
                )
                for target_factor, new_base_line in zip(target_factors, splitted_base_lines):
                    target_factor['plus_base_line']['return_of_merchandise_base_lines'].append(new_base_line)

        return [x for x in new_base_lines if x not in dispatched_neg_base_lines]