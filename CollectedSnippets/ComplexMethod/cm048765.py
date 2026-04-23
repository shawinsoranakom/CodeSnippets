def _batch_for_taxes_computation(self, special_mode=False, filter_tax_function=None):
        """ Group the current taxes all together like price-included percent taxes or division taxes.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param special_mode:        The special mode of the taxes computation: False, 'total_excluded' or 'total_included'.
        :param filter_tax_function: Optional function to filter out some taxes from the computation.
        :return: A dictionary containing:
            * batch_per_tax: A mapping of each tax to its batch.
            * group_per_tax: A mapping of each tax retrieved from a group of taxes.
            * sorted_taxes: A recordset of all taxes in the order on which they need to be evaluated.
                            Note that we consider the sequence of the parent for group of taxes.
                            Eg. considering letters as taxes and alphabetic order as sequence :
                            [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]
        """
        sorted_taxes, group_per_tax = self._flatten_taxes_and_sort_them()
        if filter_tax_function:
            sorted_taxes = sorted_taxes.filtered(filter_tax_function)

        results = {
            'batch_per_tax': {},
            'group_per_tax': group_per_tax,
            'sorted_taxes': sorted_taxes,
        }

        # Group them per batch.
        batch = self.env['account.tax']
        is_base_affected = False
        for tax in reversed(results['sorted_taxes']):
            if batch:
                same_batch = (
                    tax.amount_type == batch[0].amount_type
                    and (special_mode or tax.price_include == batch[0].price_include)
                    and tax.include_base_amount == batch[0].include_base_amount
                    and (
                        (tax.include_base_amount and not is_base_affected)
                        or not tax.include_base_amount
                    )
                )
                if not same_batch:
                    for batch_tax in batch:
                        results['batch_per_tax'][batch_tax.id] = batch
                    batch = self.env['account.tax']

            is_base_affected = tax.is_base_affected
            batch |= tax

        if batch:
            for batch_tax in batch:
                results['batch_per_tax'][batch_tax.id] = batch
        return results