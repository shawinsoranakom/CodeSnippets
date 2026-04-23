def _timesheet_postprocess_values(self, values):
        """ Get the addionnal values to write on record
            :param dict values: values for the model's fields, as a dictionary::
                {'field_name': field_value, ...}
            :return: a dictionary mapping each record id to its corresponding
                dictionary values to write (may be empty).
        """
        result = {id_: {} for id_ in self.ids}
        sudo_self = self.sudo()  # this creates only one env for all operation that required sudo()
        # (re)compute the amount (depending on unit_amount, employee_id for the cost, and account_id for currency)
        if any(field_name in values for field_name in ['unit_amount', 'employee_id', 'account_id']):
            for timesheet in sudo_self:
                if not timesheet.account_id.active:
                    project_plan, _other_plans = self.env['account.analytic.plan']._get_all_plans()
                    raise ValidationError(_(
                        "Timesheets must be created with at least an active analytic account defined in the plan '%(plan_name)s'.",
                        plan_name=project_plan.name
                    ))
                accounts = timesheet._get_analytic_accounts()
                companies = timesheet.company_id | accounts.company_id | timesheet.task_id.company_id | timesheet.project_id.company_id
                if len(companies) > 1:
                    raise ValidationError(_('The project, the task and the analytic accounts of the timesheet must belong to the same company.'))

                cost = timesheet._hourly_cost()
                amount = -timesheet.unit_amount * cost
                amount_converted = timesheet.employee_id.currency_id._convert(
                    amount, timesheet.account_id.currency_id or timesheet.currency_id, self.env.company, timesheet.date)
                result[timesheet.id].update({
                    'amount': amount_converted,
                })
        return result