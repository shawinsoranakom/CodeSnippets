def _check_amls_exigibility_for_reconciliation(self, shadowed_aml_values=None):
        """ Ensure the current journal items are eligible to be reconciled together.
        :param shadowed_aml_values: A mapping aml -> dictionary to replace some original aml values to something else.
                                    This is usefull if you want to preview the reconciliation before doing some changes
                                    on amls like changing a date or an account.
        """
        not_reconciled_partial_matching_numbers = set(self
            .filtered(lambda aml: not aml.reconciled and aml.matching_number and aml.matching_number.startswith('P'))
            .mapped('matching_number')
        )
        self = self.filtered(lambda aml: not aml.reconciled or aml.matching_number not in not_reconciled_partial_matching_numbers)

        if not self:
            return

        if any(aml.reconciled for aml in self):
            raise UserError(_("You are trying to reconcile some entries that are already reconciled."))
        if any(aml.parent_state == 'cancel' for aml in self):
            raise UserError(_("You can not reconcile cancelled entries."))
        accounts = self.mapped(lambda x: x._get_reconciliation_aml_field_value('account_id', shadowed_aml_values))
        if len(accounts) > 1:
            raise UserError(_(
                "Entries are not from the same account: %s",
                ", ".join(accounts.mapped('display_name')),
            ))
        if len(self.company_id.root_id) > 1:
            raise UserError(_(
                "Entries don't belong to the same company: %s",
                ", ".join(self.company_id.mapped('display_name')),
            ))
        if not accounts.reconcile and accounts.account_type not in ('asset_cash', 'liability_credit_card'):
            raise UserError(_(
                "Account %s does not allow reconciliation. First change the configuration of this account "
                "to allow it.",
                accounts.display_name,
            ))