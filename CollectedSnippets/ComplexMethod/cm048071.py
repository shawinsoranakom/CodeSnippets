def _split_leaves(self, split_date_from, split_date_to=False):
        """
        This method splits an original leave in two leaves and returns the new one for each leave in self.
        E.g. (start, stop) -> (start, split_date_from - 1day), (split_date_to, stop)
        :param split_date_from: The starting date of the splicing interval (includes)
        :param split_date_to: The ending date of the splicing interval. (not includes)
        :param changes_message: The message will be translated and posted in the first leave's chatter

        If split_date_to is not set; the splicing interval will be equals to [split_date_form, split_date_from -1]
        to avoid one day leave.
        """
        new_leaves_vals = []
        if not split_date_to:
            split_date_to = split_date_from

        # Only leaves that span a period outside of the split interval need
        # to be split.
        multi_day_leaves = self.filtered(lambda l: l.request_date_from < split_date_from or l.request_date_to >= split_date_to)
        for leave in multi_day_leaves:
            new_leave_vals = []
            target_leave_vals = []
            if leave.request_date_from < split_date_from:
                new_leave_vals.append(leave.with_context(skip_copy_check=True).copy_data({
                    'request_date_to': split_date_from + timedelta(days=-1),
                    'state': leave.state
                })[0])

            # Do the same for the new leave after the split
            if leave.request_date_to >= split_date_to:
                new_leave_vals.append(leave.with_context(skip_copy_check=True).copy_data({
                    'request_date_from': split_date_to,
                    'state': leave.state
                })[0])

            # For those two new leaves, only create them if they actually have a non-zero duration.
            for leave_vals in new_leave_vals:
                new_leave = self.env['hr.leave'].new(leave_vals)
                new_leave._compute_date_from_to()
                if new_leave.date_from < new_leave.date_to:
                    target_leave_vals.append(new_leave._convert_to_write(new_leave._cache))

            if target_leave_vals:
                vals = target_leave_vals.pop(0)
                leave.with_context(leave_skip_state_check=True).write({
                    'request_date_from': vals['request_date_from'],
                    'request_date_to': vals['request_date_to'],
                })
                if target_leave_vals:
                    new_leaves_vals.extend(target_leave_vals)

        if not new_leaves_vals:
            return self.env['hr.leave']
        return self.env['hr.leave'].with_context(
            tracking_disable=True,
            mail_activity_automation_skip=True,
            leave_fast_create=True,
            leave_skip_state_check=True
        ).create(new_leaves_vals)