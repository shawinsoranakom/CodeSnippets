def create(self, vals_list):
        online_account_payments_by_pm = {}
        for vals in vals_list:
            pm_id = vals['payment_method_id']
            if pm_id not in online_account_payments_by_pm:
                online_account_payments_by_pm[pm_id] = set()
            online_account_payments_by_pm[pm_id].add(vals.get('online_account_payment_id') or None)

        opms_read_id = self.env['pos.payment.method'].search_read(['&', ('id', 'in', list(online_account_payments_by_pm.keys())), ('is_online_payment', '=', True)], ["id"])
        opms_id = {opm_read_id['id'] for opm_read_id in opms_read_id}
        online_account_payments_to_check_id = set()

        for pm_id, oaps_id in online_account_payments_by_pm.items():
            if pm_id in opms_id:
                if None in oaps_id:
                    raise UserError(_("Cannot create a POS online payment without an accounting payment."))
                else:
                    online_account_payments_to_check_id.update(oaps_id)
            elif any(oaps_id):
                raise UserError(_("Cannot create a POS payment with a not online payment method and an online accounting payment."))

        if online_account_payments_to_check_id:
            valid_oap_amount = self.env['account.payment'].search_count([('id', 'in', list(online_account_payments_to_check_id))])
            if valid_oap_amount != len(online_account_payments_to_check_id):
                raise UserError(_("Cannot create a POS online payment without an accounting payment."))

        return super().create(vals_list)