def write(self, vals):
        today = fields.Date.today()

        def get_user_todo_activity_count(activities):
            return {
                user: len(user_activities.filtered(lambda a: a.active and a.date_deadline <= today))
                for user, user_activities in activities.grouped('user_id').items()
                if user
            }

        original_user_todo_activity_count = None
        if 'date_deadline' in vals or 'active' in vals or 'user_id' in vals:
            original_user_todo_activity_count = get_user_todo_activity_count(self)

        new_user_activities = self.env['mail.activity']
        if vals.get('user_id'):
            new_user_activities = self.filtered(lambda activity: activity.user_id.id != vals.get('user_id'))

        res = super().write(vals)

        # notify new responsibles
        if vals.get('user_id'):
            if vals['user_id'] != self.env.uid:
                if not self.env.context.get('mail_activity_quick_update', False):
                    new_user_activities.action_notify()
            new_user = self.env['res.users'].browse(vals['user_id'])
            for res_model, model_activities in new_user_activities.filtered(
                lambda activity: activity.res_model and activity.res_id
            ).grouped('res_model').items():
                res_ids = list(set(model_activities.mapped('res_id')))
                self.env[res_model].browse(res_ids).message_subscribe(partner_ids=new_user.partner_id.ids)

        # update activity counter
        if original_user_todo_activity_count is not None:
            new_user_todo_activity_count = get_user_todo_activity_count(self)
            for user in new_user_todo_activity_count.keys() | original_user_todo_activity_count.keys():
                count_diff = new_user_todo_activity_count.get(user, 0) - original_user_todo_activity_count.get(user, 0)
                if count_diff > 0:
                    user._bus_send("mail.activity/updated", {"activity_created": True, "count_diff": count_diff})
                elif count_diff < 0:
                    user._bus_send("mail.activity/updated", {"activity_deleted": True, "count_diff": count_diff})

        return res