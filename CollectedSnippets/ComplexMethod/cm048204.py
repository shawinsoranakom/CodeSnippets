def _get_event_track_visitors(self, force_create=False):
        self.ensure_one()

        force_visitor_create = self.env.user._is_public()
        visitor_sudo = self.env['website.visitor']._get_visitor_from_request(force_create=force_visitor_create)
        if visitor_sudo:
            visitor_sudo._update_visitor_last_visit()

        if self.env.user._is_public():
            domain = [('visitor_id', '=', visitor_sudo.id)]
        elif visitor_sudo:
            domain = [
                '|',
                ('partner_id', '=', self.env.user.partner_id.id),
                ('visitor_id', '=', visitor_sudo.id)
            ]
        else:
            domain = [('partner_id', '=', self.env.user.partner_id.id)]

        track_visitors = self.env['event.track.visitor'].sudo().search(
            Domain.AND([domain, [('track_id', 'in', self.ids)]])
        )
        missing = self - track_visitors.track_id
        if missing and force_create:
            track_visitors += self.env['event.track.visitor'].sudo().create([{
                'visitor_id': visitor_sudo.id,
                'partner_id': self.env.user.partner_id.id if not self.env.user._is_public() else False,
                'track_id': track.id,
            } for track in missing])

        return track_visitors