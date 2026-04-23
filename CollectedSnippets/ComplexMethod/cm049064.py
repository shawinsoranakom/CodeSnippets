def _perform_analytic_distribution(self, distribution, amount, unit_amount, lines, obj, additive=False):
        """
        Redistributes the analytic lines to match the given distribution:
            - For account_ids where lines already exist, the amount and unit_amount of these lines get updated,
              lines where the updated amount becomes zero get unlinked.
            - For account_ids where lines don't exist yet, the line values to create them are returned,
              lines where the amount becomes zero are not included.

        :param distribution:    the desired distribution to match the analytic lines to
        :param amount:          the total amount to distribute over the analytic lines
        :param unit_amount:     the total unit amount (will not be distributed)
        :param lines:           the (current) analytic account lines that need to be matched to the new distribution
        :param obj:             the object on which _prepare_analytic_line_values(account_id, amount, unit_amount) will be
                                called to get the template for the values of new analytic line objects
        :param additive:        if True, the unit_amount and (distributed) amount get added to the existing lines

        :returns: a list of dicts containing the values for new analytic lines that need to be created
        :rtype:   dict
        """
        if not distribution:
            lines.unlink()
            return []

        # Does this: {'15': 40, '14,16': 60} -> { account(15): 40, account(14,16): 60 }
        distribution = {
            self.env['account.analytic.account'].browse(map(int, ids.split(','))).exists(): percentage
            for ids, percentage in distribution.items()
        }

        plans = self.env['account.analytic.plan']
        plans = sum(plans._get_all_plans(), plans)
        line_columns = [p._column_name() for p in plans]

        lines_to_link = []
        distribution_on_each_plan = {}
        total_percentages = {}

        for accounts, percentage in distribution.items():
            for plan in accounts.root_plan_id:
                total_percentages[plan] = total_percentages.get(plan, 0) + percentage

        for existing_aal in lines:
            # TODO: recommend something better for this line in review, please
            accounts = sum(map(existing_aal.mapped, line_columns), self.env['account.analytic.account'])
            if accounts in distribution:
                # Update the existing AAL for this account
                percentage = distribution[accounts]
                new_amount = 0
                new_unit_amount = unit_amount
                for account in accounts:
                    plan = account.root_plan_id
                    new_amount = plan._calculate_distribution_amount(amount, percentage, total_percentages[plan], distribution_on_each_plan)
                if additive:
                    new_amount += existing_aal.amount
                    new_unit_amount += existing_aal.unit_amount
                currency = accounts[0].currency_id or obj.company_id.currency_id
                if float_is_zero(new_amount, precision_rounding=currency.rounding):
                    existing_aal.unlink()
                else:
                    existing_aal.amount = new_amount
                    existing_aal.unit_amount = new_unit_amount
                # Prevent this distribution from being applied again
                del distribution[accounts]
            else:
                # Delete the existing AAL if it is no longer present in the new distribution
                existing_aal.unlink()
        # Create new lines from remaining distributions
        for accounts, percentage in distribution.items():
            if not accounts:
                continue
            account_field_values = {}
            for account in accounts:
                new_amount = account.root_plan_id._calculate_distribution_amount(amount, percentage, total_percentages[plan], distribution_on_each_plan)
                account_field_values[account.plan_id._column_name()] = account.id
            currency = account.currency_id or obj.company_id.currency_id
            if not float_is_zero(new_amount, precision_rounding=currency.rounding):
                lines_to_link.append(obj._prepare_analytic_line_values(account_field_values, new_amount, unit_amount))
        return lines_to_link