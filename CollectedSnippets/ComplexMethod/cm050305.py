def write(self, vals):
        """Overwrite the write method to update the last_update field to today

        If the current value is changed and the report frequency is set to On
        change, a report is generated
        """
        vals['last_update'] = fields.Date.context_today(self)
        result = super().write(vals)
        for goal in self:
            if goal.state != "draft" and ('definition_id' in vals or 'user_id' in vals):
                # avoid drag&drop in kanban view
                raise exceptions.UserError(_('Can not modify the configuration of a started goal'))

            if vals.get('current') and 'no_remind_goal' not in self.env.context:
                if goal.challenge_id.report_message_frequency == 'onchange':
                    goal.challenge_id.sudo().report_progress(users=goal.user_id)
        return result