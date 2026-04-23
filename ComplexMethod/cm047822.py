def _compute_working_users(self):
        """ Checks whether the current user is working, all the users currently working and the last user that worked. """
        for order in self:
            no_date_end_times = order.time_ids.filtered(lambda time: not time.date_end).sorted('date_start')
            order.working_user_ids = [Command.link(user.id) for user in no_date_end_times.user_id]
            if order.working_user_ids:
                order.last_working_user_id = order.working_user_ids[-1]
            elif order.time_ids:
                times_with_date_end = order.time_ids.filtered('date_end').sorted('date_end')
                order.last_working_user_id = times_with_date_end[-1].user_id if times_with_date_end else order.time_ids[-1].user_id
            else:
                order.last_working_user_id = False
            if no_date_end_times.filtered(lambda x: (x.user_id.id == self.env.user.id) and (x.loss_type in ('productive', 'performance'))):
                order.is_user_working = True
            else:
                order.is_user_working = False