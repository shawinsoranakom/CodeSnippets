def _create_pm_change_log(self, vals):
        if not vals.get('payment_ids'):
            return []

        message_list = []
        new_pms = vals.get('payment_ids', [])
        for new_pm in new_pms:
            orm_command = new_pm[0]

            if orm_command == 0:
                payment_method_id = self.env['pos.payment.method'].browse(new_pm[2].get('payment_method_id'))
                amount = formatLang(self.env, new_pm[2].get('amount'), currency_obj=self.currency_id)
                message_list.append(_("Added %(payment_method)s with %(amount)s",
                    payment_method=payment_method_id.name,
                    amount=amount))
            elif orm_command == 1:
                pm_id = self.env['pos.payment'].browse(new_pm[1])
                old_pm = pm_id.payment_method_id.name
                old_amount = formatLang(self.env, pm_id.amount, currency_obj=pm_id.currency_id)
                new_amount = False
                new_payment_method = False

                if new_pm[2].get('payment_method_id'):
                    new_payment_method = self.env['pos.payment.method'].browse(new_pm[2].get('payment_method_id'))
                if new_pm[2].get('amount'):
                    new_amount = formatLang(self.env, new_pm[2].get('amount'), currency_obj=pm_id.currency_id)

                if new_payment_method and new_amount:
                    message_list.append(_("%(old_pm)s changed to %(new_pm)s and from %(old_amount)s to %(new_amount)s",
                        old_pm=old_pm,
                        new_pm=new_payment_method.name,
                        old_amount=old_amount,
                        new_amount=new_amount))
                elif new_payment_method:
                    message_list.append(_("%(old_pm)s changed to %(new_pm)s for %(old_amount)s",
                        old_pm=old_pm,
                        new_pm=new_payment_method.name,
                        old_amount=old_amount))
                elif new_amount:
                    message_list.append(_("Amount for %(old_pm)s changed from %(old_amount)s to %(new_amount)s",
                        old_amount=old_amount,
                        new_amount=new_amount,
                        old_pm=old_pm))
            elif orm_command == 2:
                pm_id = self.env['pos.payment'].browse(new_pm[1])
                amount = formatLang(self.env, pm_id.amount, currency_obj=pm_id.currency_id)
                message_list.append(_("Removed %(payment_method)s with %(amount)s",
                    payment_method=pm_id.payment_method_id.name,
                    amount=amount))

        return message_list