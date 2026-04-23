def _compute_l10n_latam_check_warning_msg(self):
        """
        Compute warning message for latam checks checks
        We use l10n_latam_check_number as de dependency because on the interface this is the field the user is using.
        Another approach could be to add an onchange on _inverse_l10n_latam_check_number method
        """
        self.l10n_latam_check_warning_msg = False
        for rec in self.filtered(lambda x: x._is_latam_check_payment()):
            msgs = rec._get_blocking_l10n_latam_warning_msg()
            # new third party check uniqueness warning (on own checks it's done by a sql constraint)
            if rec.payment_method_code == 'new_third_party_checks':
                same_checks = self.env['l10n_latam.check']
                for check in rec.l10n_latam_new_check_ids.filtered(
                        lambda x: x.name and x.payment_method_line_id.code == 'new_third_party_checks' and
                        x.bank_id and x.issuer_vat):
                    same_checks += same_checks.search([
                        ('company_id', '=', rec.company_id.id),
                        ('bank_id', '=', check.bank_id.id),
                        ('issuer_vat', '=', check.issuer_vat),
                        ('name', '=', check.name),
                        ('payment_id.state', 'not in', ['draft', 'canceled']),
                        ('id', '!=', check._origin.id)], limit=1)
                if same_checks:
                    msgs.append(
                        _("Other checks were found with same number, issuer and bank. Please double check you are not "
                          "encoding the same check more than once. List of other payments/checks: %s",
                          ", ".join(same_checks.mapped('display_name')))
                    )
            rec.l10n_latam_check_warning_msg = msgs and '* %s' % '\n* '.join(msgs) or False