def _check_lines(self):
        round_precision = self.env['decimal.precision'].precision_get('Payment Terms')
        for terms in self:
            total_percent = sum(line.value_amount for line in terms.line_ids if line.value == 'percent')
            if float_round(total_percent, precision_digits=round_precision) != 100:
                raise ValidationError(_('The Payment Term must have at least one percent line and the sum of the percent must be 100%.'))
            if len(terms.line_ids) > 1 and terms.early_discount:
                raise ValidationError(
                    _("The Early Payment Discount functionality can only be used with payment terms using a single 100% line. "))
            if terms.early_discount and terms.discount_percentage <= 0.0:
                raise ValidationError(_("The Early Payment Discount must be strictly positive."))
            if terms.early_discount and terms.discount_days <= 0:
                raise ValidationError(_("The Early Payment Discount days must be strictly positive."))