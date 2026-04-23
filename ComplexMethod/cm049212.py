def _l10n_jo_validate_fields(self):
        error_msgs = []
        if self.refunded_order_id:
            if self.refunded_order_id.l10n_jo_edi_pos_state not in ['sent', 'demo']:
                error_msgs.append(self.env._("Refunded order was not sent to JoFotara. Please submit the original order to JoFotara first and try again."))
            if not self.l10n_jo_edi_pos_return_reason:
                error_msgs.append(self.env._("Refund order must have a return reason"))
        if any(line.price_unit < 0 for line in self.lines) or (not self.refunded_order_id and any(line.qty < 0 for line in self.lines)):
            error_msgs.append(self.env._("Downpayments, global discounts, and negative lines are not supported at the moment. To revert this order, please go to Orders > Select the Order > Refund or create a Return from the backend by going to Orders > Select the Order > Return"))
        if not self._l10n_jo_edi_pos_get_payment_type():
            error_msgs.append(self.env._("Please select the payment methods that are consistent with the value set in 'JoFotara Cash'. If set, the payment method is Cash. If empty, then it is Receivable."))
        else:
            jod = self.env.ref('base.JOD')
            amount_total_jod = self.amount_total if self.currency_id == jod else self.currency_id._convert(self.amount_total, jod, self.company_id, self.date_order)
            amount_total_requires_customer = jod.compare_amounts(amount_total_jod, 10_000) == 1
            if not self.partner_id and (self._l10n_jo_edi_pos_get_payment_type() == 'receivable' or amount_total_requires_customer):
                error_msgs.append(self.env._("Customer is required on either Receivable or more than 10,000 JOD Cash Orders."))

        for line in self.lines:
            if self.company_id.l10n_jo_edi_taxpayer_type == 'income' and len(line.tax_ids) != 0:
                error_msgs.append(self.env._("No taxes are allowed on order lines for taxpayers unregistered in the sales tax"))
            elif self.company_id.l10n_jo_edi_taxpayer_type == 'sales' and len(line.tax_ids) != 1:
                error_msgs.append(self.env._("One general tax per order line is expected for taxpayers registered in the sales tax"))
            elif self.company_id.l10n_jo_edi_taxpayer_type == 'special' and len(line.tax_ids) != 2:
                error_msgs.append(self.env._("One special and one general tax per order line are expected for taxpayers registered in the special tax"))

        return "\n".join(error_msgs)