def _compute_website_track(self):
        """ Propagate event_type configuration (only at change); otherwise propagate
        website_menu updated value. Also force True is track_proposal changes. """
        for event in self:
            if event.event_type_id and event.event_type_id != event._origin.event_type_id:
                event.website_track = event.event_type_id.website_track
            elif event.website_menu and (event.website_menu != event._origin.website_menu or not event.website_track):
                event.website_track = True
            elif not event.website_menu:
                event.website_track = False