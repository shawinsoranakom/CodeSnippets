def _fetch_query(self, query, fields):
        if self.env.su:
            return super()._fetch_query(query, fields)

        public_fnames = self._get_public_fields()
        private_fields = [field for field in fields if field.name not in public_fnames]
        if not private_fields:
            return super()._fetch_query(query, fields)

        fields_to_fetch = list(fields) + [self._fields[name] for name in ('privacy', 'user_id', 'partner_ids')]
        events = super()._fetch_query(query, fields_to_fetch)

        # determine private events to which the user does not participate
        others_private_events = events.filtered(lambda ev: ev._check_private_event_conditions())
        if not others_private_events:
            return events

        private_fields.append(self._fields['partner_ids'])
        for field in private_fields:
            replacement = field.convert_to_cache(
                _('Busy') if field.name == 'name' else False,
                others_private_events)
            self.env.cache.update(others_private_events, field, repeat(replacement))

        return events