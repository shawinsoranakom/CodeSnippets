def _validate_withholding(self):
        for tax in self:
            if tax.l10n_it_withholding_type and tax.amount >= 0:
                raise ValidationError(_("Tax '%s' has a withholding type so the amount must be negative.", tax.name))
            if tax.l10n_it_withholding_type and not tax.l10n_it_withholding_reason:
                raise ValidationError(_("Tax '%s' has a withholding type, so the withholding reason must also be specified", tax.name))
            if tax.l10n_it_withholding_reason and not tax.l10n_it_withholding_type:
                raise ValidationError(_("Tax '%s' has a withholding reason, so the withholding type must also be specified", tax.name))
            if (tax.l10n_it_withholding_type == 'RT04') ^ (tax.l10n_it_pension_fund_type == 'TC07'):
                raise ValidationError(_("Tax '%s' has one of withholding and pension fund types that do not relate to ENASARCO, and one that does.", tax.name))
            if tax.l10n_it_withholding_type == 'RT04' and tax.l10n_it_withholding_reason != 'ZO':
                raise ValidationError(_("Tax '%s' has withholding type ENASARCO, the withholding reason should be [ZO] - Other reason.", tax.name))