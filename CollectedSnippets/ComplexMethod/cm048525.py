def _get_group_name(self):
        """ Return a human-readable name for a wizard line's group, based on its `account_id`, in the format:
        '{Trade/Non-trade} Receivable {USD} {Reconcilable} {Deprecated}'
        """
        self.ensure_one()

        account_type_label = dict(self.pool['account.account'].account_type._description_selection(self.env))[self.account_id.account_type]
        if self.account_id.account_type in ['asset_receivable', 'liability_payable']:
            account_type_label = _("Non-trade %s", account_type_label) if self.account_id.non_trade else _("Trade %s", account_type_label)

        other_name_elements = []
        if self.account_id.currency_id:
            other_name_elements.append(self.account_id.currency_id.name)

        if self.account_id.reconcile:
            other_name_elements.append(_("Reconcilable"))

        if not self.account_id.active:
            other_name_elements.append(_("Deprecated"))

        if not self.wizard_id.is_group_by_name:
            grouping_key_name = account_type_label
            if other_name_elements:
                grouping_key_name = f'{grouping_key_name} ({", ".join(other_name_elements)})'
        else:
            grouping_key_name = f'{self.account_id.name} ({", ".join([account_type_label] + other_name_elements)})'

        return grouping_key_name