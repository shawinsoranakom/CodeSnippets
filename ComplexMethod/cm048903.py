def _get_blocking_l10n_latam_warning_msg(self):
        msgs = []
        for rec in self.filtered(lambda x: x.state == 'draft' and x._is_latam_check_payment()):
            if any(rec.currency_id != check.currency_id for check in rec._get_latam_checks()):
                msgs.append(_('The currency of the payment and the currency of the check must be the same.'))
            if not rec.currency_id.is_zero(sum(rec._get_latam_checks().mapped('amount')) - rec.amount):
                msgs.append(
                    _('The amount of the payment  does not match the amount of the selected check. '
                      'Please try to deselect and select the check again.')
                )
            # checks being moved
            if rec._is_latam_check_payment(check_subtype='move_check'):
                if any(check.payment_id.state == 'draft' for check in rec.l10n_latam_move_check_ids):
                    msgs.append(
                        _('Selected checks "%s" are not posted', rec.l10n_latam_move_check_ids.filtered(lambda x: x.payment_id.state == 'draft').mapped('display_name'))
                    )
                elif rec.payment_type == 'outbound' and any(check.current_journal_id != rec.journal_id for check in rec.l10n_latam_move_check_ids):
                    # check outbound payment and transfer or inbound transfer
                    msgs.append(_(
                        'Some checks are not anymore in journal, it seems it has been moved by another payment.')
                    )
                elif rec.payment_type == 'inbound' and not rec._is_latam_check_transfer() and any(rec.l10n_latam_move_check_ids.mapped('current_journal_id')):
                    msgs.append(
                        _("Some checks are already in hand and can't be received again. Checks: %s",
                          ', '.join(rec.l10n_latam_move_check_ids.mapped('display_name')))
                    )

                for check in rec.l10n_latam_move_check_ids:
                    date = rec.date or fields.Datetime.now()

                    last_operation = check._get_last_operation()
                    if last_operation and last_operation[0].date > date:
                        msgs.append(
                            _(
                              "It seems you're trying to move a check with a date (%(date)s) prior to last "
                              "operation done with the check (%(last_operation)s). This may be wrong, please "
                              "double check it. By continue, the last operation on "
                              "the check will remain being %(last_operation)s",
                              date=format_date(self.env, date), last_operation=last_operation.display_name
                            )
                        )
        return msgs