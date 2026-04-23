def _prepare_reconciliation_amls(self, values_list, shadowed_aml_values=None):
        """ Prepare the partials on the current journal items to perform the reconciliation.
        Note: The order of records in self is important because the journal items will be reconciled using this order.

        :param values_list: A list of dictionaries, one for each aml.
        :param shadowed_aml_values: A mapping aml -> dictionary to replace some original aml values to something else.
                                    This is usefull if you want to preview the reconciliation before doing some changes
                                    on amls like changing a date or an account.
        :return: a tuple of
            1) list of vals for partial reconciliation creation,
            2) the list of vals for the exchange difference entries to be created
        """
        debit_values_list = iter([
            x
            for x in values_list
            if x['aml']._get_reconciliation_aml_field_value('balance', shadowed_aml_values) > 0.0
               or x['aml']._get_reconciliation_aml_field_value('amount_currency', shadowed_aml_values) > 0.0
        ])
        credit_values_list = iter([
            x
            for x in values_list
            if x['aml']._get_reconciliation_aml_field_value('balance', shadowed_aml_values) < 0.0
               or x['aml']._get_reconciliation_aml_field_value('amount_currency', shadowed_aml_values) < 0.0
        ])
        debit_values = None
        credit_values = None
        fully_reconciled_aml_ids = set()

        all_results = []
        while True:

            # ==== Find the next available lines ====
            # For performance reasons, the partials are created all at once meaning the residual amounts can't be
            # trusted from one iteration to another. That's the reason why all residual amounts are kept as variables
            # and reduced "manually" every time we append a dictionary to 'partials_values_list'.

            # Move to the next available debit line.
            if not debit_values:
                debit_values = next(debit_values_list, None)
                if not debit_values:
                    break

            # Move to the next available credit line.
            if not credit_values:
                credit_values = next(credit_values_list, None)
                if not credit_values:
                    break

            # ==== Compute the amounts to reconcile ====

            results = self._prepare_reconciliation_single_partial(
                debit_values,
                credit_values,
                shadowed_aml_values=shadowed_aml_values,
            )
            if results.get('partial_values'):
                all_results.append(results)
            if results['debit_values'] is None:
                fully_reconciled_aml_ids.add(debit_values['aml'].id)
                debit_values = None
            if results['credit_values'] is None:
                fully_reconciled_aml_ids.add(credit_values['aml'].id)
                credit_values = None

        return all_results, fully_reconciled_aml_ids