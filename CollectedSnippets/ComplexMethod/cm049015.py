def _check_unicity(self):
        """Check that the link trackers are unique."""
        def _format_value(tracker, field_name):
            if field_name == 'label' and not tracker[field_name]:
                return False
            return tracker[field_name]

        # build a query to fetch all needed link trackers at once
        search_query = Domain.OR([
            Domain.AND([
                [('url', '=', tracker.url)],
                [('campaign_id', '=', tracker.campaign_id.id)],
                [('medium_id', '=', tracker.medium_id.id)],
                [('source_id', '=', tracker.source_id.id)],
                [('label', '=', tracker.label) if tracker.label else ('label', 'in', (False, ''))],
            ])
            for tracker in self
        ])

        # Can not be implemented with a SQL constraint because we care about null values.
        potential_duplicates = self.search(search_query)
        duplicates = self.browse()
        seen = set()
        for tracker in potential_duplicates:
            unique_fields = tuple(_format_value(tracker, field_name) for field_name in LINK_TRACKER_UNIQUE_FIELDS)
            if unique_fields in seen or seen.add(unique_fields):
                duplicates += tracker
        if duplicates:
            error_lines = '\n- '.join(
                str((tracker.url, tracker.campaign_id.name, tracker.medium_id.name, tracker.source_id.name, tracker.label or '""'))
                for tracker in duplicates
            )
            raise UserError(
                _('Combinations of Link Tracker values (URL, campaign, medium, source, and label) must be unique.\n'
                  'The following combinations are already used: \n- %(error_lines)s', error_lines=error_lines))