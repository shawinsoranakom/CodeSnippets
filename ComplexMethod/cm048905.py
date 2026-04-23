def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        """ Add check name and operation on liquidity line """
        res = super()._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals, force_balance=force_balance)

        # if only one check we don't create the split line, we add same data on liquidity line
        if self.payment_method_code == 'own_checks' and self.payment_type == 'outbound' and len(self.l10n_latam_new_check_ids) == 1:
            res[0].update({
                'name': _(
                    'Check %(check_number)s - %(suffix)s',
                    check_number=self.l10n_latam_new_check_ids.name,
                    suffix=''.join([item[1] for item in self._get_aml_default_display_name_list()])),
                'date_maturity': self.l10n_latam_new_check_ids.payment_date,
            })
        # we dont check the payment method code because when deposited on bank/cash journals pay method is manual but we still change the label
        # we dont want this names on the own checks because it doesn't add value, already each split/check line will have it name
        elif (self.l10n_latam_new_check_ids or self.l10n_latam_move_check_ids) and self.payment_method_code != 'own_checks':
            check_name = [check_name for check_name in (self.l10n_latam_new_check_ids | self.l10n_latam_move_check_ids).mapped('name') if check_name]
            document_name = (
                _('Checks %s received') if self.payment_type == 'inbound' else _('Checks %s delivered')) % (
                ', '.join(check_name)
            )
            res[0].update({
                'name': document_name + ' - ' + ''.join([item[1] for item in self._get_aml_default_display_name_list()]),
            })
        return res