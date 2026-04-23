def _get_events_delta(self, sync_token=None, token=None, timeout=TIMEOUT):
        """
        Get a set of events that have been added, deleted or updated in a time range.
        See: https://docs.microsoft.com/en-us/graph/api/event-delta?view=graph-rest-1.0&tabs=http
        """
        url = "/v1.0/me/calendarView/delta"
        params = {'$deltatoken': sync_token} if sync_token else None

        try:
            events, next_sync_token = self._get_events_from_paginated_url(
                url, params=params, token=token, timeout=timeout)
        except requests.HTTPError as e:
            full_sync_needed = self._check_full_sync_required(e.response)
            if e.response.status_code == 410 and full_sync_needed and sync_token:
                # retry with a full sync
                return self._get_events_delta(token=token, timeout=timeout)
            raise e

        # event occurrences (from a recurrence) are retrieved separately to get all their info,
        # # and mainly the iCalUId attribute which is not provided by the 'get_delta' api end point
        events = [e for e in events if e.get('type') != 'occurrence']

        return MicrosoftEvent(events), next_sync_token