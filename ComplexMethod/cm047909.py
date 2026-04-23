def _modifiying_distribution_values(self, old_distribution, new_distribution):
        fnames_to_update = set(new_distribution.pop('__update__', ()))
        if old_distribution:
            old_distribution.pop('__update__', None)  # might be set before in `create`
        project_plan, other_plans = self.env['account.analytic.plan']._get_all_plans()
        non_changing_plans = {
            plan
            for plan in project_plan + other_plans
            if plan._column_name() not in fnames_to_update
        }

        non_changing_values = defaultdict(float)
        non_changing_amount = 0
        for old_key, old_val in old_distribution.items():
            remaining_key = tuple(sorted(
                account.id
                for account in self.env['account.analytic.account'].browse(int(aid) for aid in old_key.split(','))
                if account.plan_id.root_id in non_changing_plans
            ))
            if remaining_key:
                non_changing_values[remaining_key] += old_val
                non_changing_amount += old_val

        changing_values = defaultdict(float)
        changing_amount = 0
        for new_key, new_val in new_distribution.items():
            remaining_key = tuple(sorted(
                account.id
                for account in self.env['account.analytic.account'].browse(int(aid) for aid in new_key.split(','))
                if account.plan_id.root_id not in non_changing_plans
            ))
            if remaining_key:
                changing_values[remaining_key] += new_val
                changing_amount += new_val

        return non_changing_values, changing_values, non_changing_amount, changing_amount