def _compute_installments_switch_values(self):
        for wizard in self:
            if not wizard.journal_id or not wizard.currency_id:
                wizard.installments_switch_amount = wizard.installments_switch_amount
                wizard.installments_switch_html = wizard.installments_switch_html
            else:
                total_amount_values = wizard._get_total_amounts_to_pay(wizard.batches)
                html_lines = []
                if wizard.installments_mode == 'full':
                    is_full_match = (
                        wizard.currency_id.is_zero(total_amount_values['full_amount'] - wizard.amount)
                        and wizard.currency_id.is_zero(total_amount_values['full_amount'] - total_amount_values['amount_by_default'])
                    )
                    wizard.installments_switch_amount = 0.0 if is_full_match else total_amount_values['amount_by_default']
                    if not is_full_match and not wizard.currency_id.is_zero(wizard.amount):
                        switch_message = (
                            _("Consider paying the amount with %(btn_start)searly payment discount%(btn_end)s instead.")
                            if total_amount_values['epd_applied']
                            else _("Consider paying in %(btn_start)sinstallments%(btn_end)s instead.")
                        )
                        html_lines += [
                            _("This is the full amount."),
                            switch_message,
                        ]
                elif wizard.installments_mode == 'overdue':
                    wizard.installments_switch_amount = total_amount_values['full_amount']
                    html_lines += [
                        _("This is the overdue amount."),
                        _("Consider paying the %(btn_start)sfull amount%(btn_end)s."),
                    ]
                elif wizard.installments_mode == 'before_date':
                    wizard.installments_switch_amount = total_amount_values['full_amount']
                    next_payment_date = self._get_next_payment_date_in_context()
                    html_lines += [
                        _("Total for the installments before %(date)s.", date=(next_payment_date or fields.Date.context_today(self))),
                        _("Consider paying the %(btn_start)sfull amount%(btn_end)s."),
                    ]
                elif wizard.installments_mode == 'next':
                    wizard.installments_switch_amount = total_amount_values['full_amount']
                    html_lines += [
                        _("This is the next unreconciled installment."),
                        _("Consider paying the %(btn_start)sfull amount%(btn_end)s."),
                    ]
                else:
                    wizard.installments_switch_amount = wizard.installments_switch_amount

                if wizard.custom_user_amount:
                    wizard.installments_switch_html = None
                else:
                    wizard.installments_switch_html = markupsafe.Markup('<br/>').join(html_lines) % {
                        'btn_start': markupsafe.Markup('<span class="installments_switch_button btn btn-link p-0 align-baseline">'),
                        'btn_end': markupsafe.Markup('</span>'),
                    }