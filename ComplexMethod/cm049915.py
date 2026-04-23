def _run_action_next_activity(self, eval_context=None):
        if not self.activity_type_id or not self.env.context.get('active_id') or self._is_recompute():
            return False

        records = self.env[self.model_name].browse(self.env.context.get('active_ids', self.env.context.get('active_id')))

        vals = {
            'summary': self.activity_summary or '',
            'note': self.activity_note or '',
            'activity_type_id': self.activity_type_id.id,
        }
        if self.activity_date_deadline_range > 0:
            vals['date_deadline'] = fields.Date.context_today(self) + relativedelta(**{
                self.activity_date_deadline_range_type or 'days': self.activity_date_deadline_range})
        for record in records:
            user = False
            if self.activity_user_type == 'specific':
                user = self.activity_user_id
            elif self.activity_user_type == 'generic' and self.activity_user_field_name in record:
                user = record[self.activity_user_field_name]
            if user:
                # if x2m field, assign to the first user found
                # (same behavior as Field.traverse_related)
                vals['user_id'] = user.ids[0]
            record.activity_schedule(**vals)
        return False