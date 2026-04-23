def _sync_activities(self, fields):
        # update activities
        for event in self:
            if event.activity_ids:
                activity_values = {}
                if 'name' in fields:
                    activity_values['summary'] = event.name
                if 'description' in fields:
                    activity_values['note'] = event.description
                # protect against loops in case of ill-managed timezones
                if 'start' in fields and not self.env.context.get('mail_activity_meeting_update'):
                    activity_values['date_deadline'] = self._get_activity_deadline_from_start(event.start, event.allday)
                if 'user_id' in fields:
                    activity_values['user_id'] = event.user_id.id
                if activity_values.keys():
                    event.activity_ids.write(activity_values)