def _inverse_analytic_distribution(self):
        empty_account = dict.fromkeys(self._get_plan_fnames(), False)
        to_create_vals = []
        for line in self:
            final_distribution = self.env['analytic.mixin']._merge_distribution(
                {line._get_distribution_key(): 100},
                line.analytic_distribution or {},
            )
            if not final_distribution:
                continue
            amount_fname = line._split_amount_fname()
            vals_list = [
                {amount_fname: line[amount_fname] * percent / 100} | empty_account | {
                    account.plan_id._column_name(): account.id
                    for account in self.env['account.analytic.account'].browse(int(aid) for aid in account_ids.split(','))
                }
                for account_ids, percent in final_distribution.items()
            ]

            line.write(vals_list[0])
            to_create_vals += [line.copy_data(vals)[0] for vals in vals_list[1:]]
        if to_create_vals:
            self.create(to_create_vals)
            self.env.user._bus_send('simple_notification', {
                'type': 'success',
                'message': self.env._("%s analytic lines created", len(to_create_vals)),
            })