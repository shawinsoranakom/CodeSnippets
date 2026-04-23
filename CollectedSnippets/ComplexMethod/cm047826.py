def button_start(self, raise_on_invalid_state=False):
        if any(wo.working_state == 'blocked' for wo in self):
            raise UserError(_('Please unblock the work center to start the work order.'))
        for wo in self:
            if any(not time.date_end for time in wo.time_ids.filtered(lambda t: t.user_id.id == self.env.user.id)):
                continue
            if wo.state in ('done', 'cancel'):
                if raise_on_invalid_state:
                    continue
                raise UserError(_('You cannot start a work order that is already done or cancelled'))

            if wo.qty_producing == 0:
                wo.qty_producing = wo.qty_remaining

            if wo._should_start_timer():
                self.env['mrp.workcenter.productivity'].create(
                    wo._prepare_timeline_vals(wo.duration, fields.Datetime.now())
                )

            if wo.production_id.state != 'progress':
                wo.production_id.write({
                    'date_start': fields.Datetime.now()
                })
            if wo.state == 'progress':
                continue
            date_start = fields.Datetime.now()
            vals = {
                'state': 'progress',
                'date_start': date_start,
            }
            if not wo.leave_id:
                leave = self.env['resource.calendar.leaves'].create({
                    'name': wo.display_name,
                    'calendar_id': wo.workcenter_id.resource_calendar_id.id,
                    'date_from': date_start,
                    'date_to': date_start + relativedelta(minutes=wo.duration_expected),
                    'resource_id': wo.workcenter_id.resource_id.id,
                    'time_type': 'other'
                })
                vals['date_finished'] = leave.date_to
                vals['leave_id'] = leave.id
                wo.write(vals)
            else:
                if not wo.date_start or wo.date_start > date_start:
                    vals['date_finished'] = wo._calculate_date_finished(date_start)
                if wo.date_finished and wo.date_finished < date_start:
                    vals['date_finished'] = date_start
                wo.with_context(bypass_duration_calculation=True).write(vals)