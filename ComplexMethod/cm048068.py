def _unlink_if_correct_states(self):
        error_message = self.env._('Oops! %(state)s Time-Off requests can only be deleted by Administrators.')
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        now = fields.Datetime.now().date()

        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            for hol in self:
                if hol.state not in ['confirm', 'validate1', 'cancel']:
                    raise UserError(error_message % {'state': state_description_values.get(self[:1].state)})
                if hol.date_from.date() < now:
                    raise UserError(_("You can't delete a time off request that is in the past."))
        elif not self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
            for holiday in self.filtered(lambda holiday: holiday.state not in ['cancel', 'confirm']):
                error_message = self.env._('Oops! %(state)s Time-Off requests can only be deleted by Administrators.')
                raise UserError(error_message % {'state': state_description_values.get(holiday.state)})