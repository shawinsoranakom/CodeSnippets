def _event_tracks_get_values(self, event, tag=None, **searches):
        # init and process search terms
        searches.setdefault('search', '')
        searches.setdefault('search_wishlist', '')
        searches.setdefault('tags', '')
        search_domain = self._get_event_tracks_agenda_domain(event)

        # search on content
        if searches.get('search'):
            search_domain = Domain.AND([
                search_domain,
                ['|', ('name', 'ilike', searches['search']), ('partner_name', 'ilike', searches['search'])]
            ])

        # search on tags
        search_tags = self._get_search_tags(searches['tags'])
        if not search_tags and tag:  # backward compatibility
            search_tags = tag
        if search_tags:
            # Example: You filter on age: 10-12 and activity: football.
            # Doing it this way allows to only get events who are tagged "age: 10-12" AND "activity: football".
            # Add another tag "age: 12-15" to the search and it would fetch the ones who are tagged:
            # ("age: 10-12" OR "age: 12-15") AND "activity: football
            grouped_tags = dict()
            for search_tag in search_tags:
                grouped_tags.setdefault(search_tag.category_id, list()).append(search_tag)
            search_domain_items = [
                [('tag_ids', 'in', [tag.id for tag in grouped_tags[group]])]
                for group in grouped_tags
            ]
            search_domain = Domain.AND([
                search_domain,
                *search_domain_items
            ])

        # fetch data to display with TZ set for both event and tracks
        now_tz = utc.localize(fields.Datetime.now().replace(microsecond=0), is_dst=False).astimezone(timezone(event.date_tz))
        today_tz = now_tz.date()
        event = event.with_context(tz=event.date_tz or 'UTC')
        tracks_sudo = event.env['event.track'].sudo().search(search_domain, order='is_published desc, date asc')
        tag_categories = request.env['event.track.tag.category'].sudo().search([])

        # filter on wishlist (as post processing due to costly search on is_reminder_on)
        if searches.get('search_wishlist'):
            tracks_sudo = tracks_sudo.filtered(lambda track: track.is_reminder_on)

        # organize categories for display: announced, live, soon and day-based
        tracks_announced = tracks_sudo.filtered(lambda track: not track.date)
        tracks_wdate = tracks_sudo - tracks_announced
        date_begin_tz_all = list(set(
            dt.date()
            for dt in self._get_dt_in_event_tz(tracks_wdate.mapped('date'), event)
        ))
        date_begin_tz_all.sort()
        tracks_sudo_live = tracks_wdate.filtered(lambda track: track.is_track_live)
        tracks_sudo_soon = tracks_wdate.filtered(lambda track: not track.is_track_live and track.is_track_soon)
        tracks_by_day = []
        for display_date in date_begin_tz_all:
            matching_tracks = tracks_wdate.filtered(lambda track: self._get_dt_in_event_tz([track.date], event)[0].date() == display_date)
            tracks_by_day.append({'date': display_date, 'name': display_date, 'tracks': matching_tracks})
        if tracks_announced:
            tracks_announced = tracks_announced.sorted('wishlisted_by_default', reverse=True)
            tracks_by_day.append({'date': False, 'name': _('Coming soon'), 'tracks': tracks_announced})
        # Check if there are any ongoing or upcoming tracks
        has_upcoming_or_ongoing = any(track for track in tracks_sudo if not track.is_track_done)

        for tracks_group in tracks_by_day:
           tracks_group['default_collapsed'] = (
                has_upcoming_or_ongoing and
                tracks_group['date'] and all(track.is_track_done for track in tracks_group['tracks'])
            )

        # return rendering values
        return {
            # event information
            'event': event,
            'main_object': event,
            'slots': event.event_slot_ids._filter_open_slots().grouped('date'),
            # tracks display information
            'tracks': tracks_sudo,
            'tracks_by_day': tracks_by_day,
            'tracks_live': tracks_sudo_live,
            'tracks_soon': tracks_sudo_soon,
            'today_tz': today_tz,
            # search information
            'searches': searches,
            'search_count': len(tracks_sudo),
            'search_key': searches['search'],
            'search_wishlist': searches['search_wishlist'],
            'search_tags': search_tags,
            'tag_categories': tag_categories,
            # environment
            'is_html_empty': is_html_empty,
            'hostname': request.httprequest.host.split(':')[0],
            'is_event_user': request.env.user.has_group('event.group_event_user'),
            'website_visitor_timezone': request.env['website.visitor']._get_visitor_timezone(),
        }