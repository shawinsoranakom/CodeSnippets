def get_events(self, sync_token=None, token=None, event_id=None, timeout=TIMEOUT):
        url = "/calendar/v3/calendars/primary/events"
        if event_id:
            url += f"/{event_id}"
        headers = {'Content-type': 'application/json'}
        params = {'access_token': token}
        if sync_token:
            params['syncToken'] = sync_token
        else:
            # full sync, limit to a range of 1y in past to 1y in the futur by default
            ICP = self.google_service.env['ir.config_parameter'].sudo()
            day_range = int(ICP.get_param('google_calendar.sync.range_days', default=365))
            _logger.info("Full cal sync, restricting to %s days range", day_range)
            lower_bound = fields.Datetime.subtract(fields.Datetime.now(), days=day_range)
            upper_bound = fields.Datetime.add(fields.Datetime.now(), days=day_range)
            params['timeMin'] = lower_bound.isoformat() + 'Z'  # Z = UTC (RFC3339)
            params['timeMax'] = upper_bound.isoformat() + 'Z'  # Z = UTC (RFC3339)
        try:
            status, data, time = self.google_service._do_request(url, params, headers, method='GET', timeout=timeout)
        except requests.HTTPError as e:
            if e.response.status_code == 410 and 'fullSyncRequired' in str(e.response.content):
                raise InvalidSyncToken("Invalid sync token. Full sync required")
            raise e

        if event_id:
            next_sync_token = None
            default_reminders = ()
            return GoogleEvent([data]), next_sync_token, default_reminders

        events = data.get('items', [])
        next_page_token = data.get('nextPageToken')
        while next_page_token:
            params = {'access_token': token, 'pageToken': next_page_token}
            status, data, time = self.google_service._do_request(url, params, headers, method='GET', timeout=timeout)
            next_page_token = data.get('nextPageToken')
            events += data.get('items', [])

        next_sync_token = data.get('nextSyncToken')
        default_reminders = data.get('defaultReminders')

        return GoogleEvent(events), next_sync_token, default_reminders