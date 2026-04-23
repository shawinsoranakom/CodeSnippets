def write(self, vals):
        # Overridden to reset the kanban_state to normal whenever
        # the stage (stage_id) of the Maintenance Request changes.
        if vals and 'kanban_state' not in vals and 'stage_id' in vals:
            vals['kanban_state'] = 'normal'
        now = fields.Datetime.now()
        if 'stage_id' in vals and self.env['maintenance.stage'].browse(vals['stage_id']).done:
            for request in self:
                if request.maintenance_type != 'preventive' or not request.recurring_maintenance:
                    continue
                schedule_date = request.schedule_date or now
                schedule_date += relativedelta(**{f"{request.repeat_unit}s": request.repeat_interval})
                schedule_end = schedule_date + relativedelta(hours=request.duration or 1)
                if request.repeat_type == 'forever' or schedule_date.date() <= request.repeat_until:
                    request.copy({
                        'schedule_date': schedule_date,
                        'schedule_end': schedule_end,
                        'stage_id': request._default_stage().id,
                    })
        res = super(MaintenanceRequest, self).write(vals)
        if vals.get('owner_user_id') or vals.get('user_id'):
            self._add_followers()
        if 'stage_id' in vals:
            self.filtered(lambda m: m.stage_id.done).write({'close_date': fields.Date.today()})
            self.filtered(lambda m: not m.stage_id.done).write({'close_date': False})
            self.activity_feedback(['maintenance.mail_act_maintenance_request'])
            self.activity_update()
        if vals.get('user_id') or vals.get('schedule_date'):
            self.activity_update()
        if self._need_new_activity(vals):
            # need to change description of activity also so unlink old and create new activity
            self.activity_unlink(['maintenance.mail_act_maintenance_request'])
            self.activity_update()
        return res