def activity_reschedule(self, act_type_xmlids, user_id=None, date_deadline=None, new_user_id=None, only_automated=True):
        """ Reschedule some automated activities. Activities to reschedule are
        selected based on type xml ids and optionally by user. Purpose is to be
        able to

         * update the deadline to date_deadline;
         * update the responsible to new_user_id;
        """
        if self.env.context.get('mail_activity_automation_skip'):
            return False

        Data = self.env['ir.model.data'].sudo()
        activity_types_ids = [Data._xmlid_to_res_id(xmlid, raise_if_not_found=False) for xmlid in act_type_xmlids]
        activity_types_ids = [act_type_id for act_type_id in activity_types_ids if act_type_id]
        if not any(activity_types_ids):
            return False
        activities = self.activity_search(act_type_xmlids, user_id=user_id, only_automated=only_automated)
        if activities:
            write_vals = {}
            if date_deadline:
                write_vals['date_deadline'] = date_deadline
            if new_user_id:
                write_vals['user_id'] = new_user_id
            activities.write(write_vals)
        return activities