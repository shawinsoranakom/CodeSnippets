def write(self, vals):
        date_from, date_to, calendar_id = vals.get('date_from'), vals.get('date_to'), vals.get('calendar_id')
        global_time_off_updated = self.env['resource.calendar.leaves']
        overlapping_leaves = self.env['hr.leave']
        if date_from or date_to or 'calendar_id' in vals:
            global_time_off_updated = self.filtered(lambda r: (date_from is not None and r.date_from != date_from) or (date_to is not None and r.date_to != date_to) or (calendar_id is None or r.calendar_id.id != calendar_id))
            timesheets = global_time_off_updated.sudo().timesheet_ids
            if timesheets:
                timesheets.write({'global_leave_id': False})
                timesheets.unlink()
            if calendar_id:
                for gto in global_time_off_updated:
                    domain = [] if gto.calendar_id else [('resource_calendar_id', '!=', calendar_id)]
                    overlapping_leaves += gto._get_overlapping_hr_leaves(domain)
        result = super().write(vals)
        global_time_off_updated and global_time_off_updated.sudo()._generate_timesheeets()
        if overlapping_leaves:
            overlapping_leaves.sudo()._generate_timesheets()
        return result