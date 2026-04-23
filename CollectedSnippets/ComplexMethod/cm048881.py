def create(self, vals_list):
        user_ids = {v['user_id'] for v in vals_list if v.get('user_id')}
        users_with_sync = self.env['res.users'].browse(user_ids).filtered(lambda u: not u.sudo().google_synchronization_stopped)
        users_with_sync_set = set(users_with_sync.ids)

        for vals in vals_list:
            if vals.get('user_id', False) and vals['user_id'] not in users_with_sync_set:
                vals.update({'need_sync': False})
        records = super().create(vals_list)
        self._handle_allday_recurrences_edge_case(records, vals_list)

        google_service = GoogleCalendarService(self.env['google.service'])
        if self.env.user._get_google_sync_status() != "sync_paused":
            for record in records:
                if record.need_sync and record.active:
                    record.with_user(record._get_event_user())._google_insert(google_service, record._google_values(), timeout=3)
        return records