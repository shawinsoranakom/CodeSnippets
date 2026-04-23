def _plan_workorder(self, replan=False):
        self.ensure_one()
        # Plan workorder after its predecessors
        date_start = max(self.production_id.date_start, datetime.now())
        for workorder in self.blocked_by_workorder_ids:
            workorder._plan_workorder(replan)
            if workorder.date_finished and workorder.date_finished > date_start:
                date_start = workorder.date_finished
        # Plan only suitable workorders
        if self.state not in ['blocked', 'ready']:
            return
        if self.leave_id:
            if replan:
                self.leave_id.unlink()
            else:
                return
        # Consider workcenter and alternatives
        workcenters = self.workcenter_id | self.workcenter_id.alternative_workcenter_ids
        best_date_finished = datetime.max
        vals = {}
        for workcenter in workcenters:
            if not workcenter.resource_calendar_id:
                raise UserError(_('There is no defined calendar on workcenter %s.', workcenter.name))
            # Compute theoretical duration
            if self.workcenter_id == workcenter:
                duration_expected = self.duration_expected
            else:
                duration_expected = self._get_duration_expected(alternative_workcenter=workcenter)
            from_date, to_date = workcenter._get_first_available_slot(date_start, duration_expected)
            # If the workcenter is unavailable, try planning on the next one
            if not from_date:
                continue
            # Check if this workcenter is better than the previous ones
            if to_date and to_date < best_date_finished:
                best_date_start = from_date
                best_date_finished = to_date
                best_workcenter = workcenter
                vals = {
                    'workcenter_id': workcenter.id,
                    'duration_expected': duration_expected,
                }
        # If none of the workcenter are available, raise
        if best_date_finished == datetime.max:
            raise UserError(_('Impossible to plan the workorder. Please check the workcenter availabilities.'))
        # Create leave on chosen workcenter calendar
        leave = self.env['resource.calendar.leaves'].create({
            'name': self.display_name,
            'calendar_id': best_workcenter.resource_calendar_id.id,
            'date_from': best_date_start,
            'date_to': best_date_finished,
            'resource_id': best_workcenter.resource_id.id,
            'time_type': 'other'
        })
        vals['leave_id'] = leave.id
        self.write(vals)