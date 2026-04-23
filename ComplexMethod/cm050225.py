def _compute_exhibitor_menu(self):
        for event in self:
            if event.event_type_id and event.event_type_id != event._origin.event_type_id:
                event.exhibitor_menu = event.event_type_id.exhibitor_menu
            elif event.website_menu and (event.website_menu != event._origin.website_menu or not event.exhibitor_menu):
                event.exhibitor_menu = True
            elif not event.website_menu:
                event.exhibitor_menu = False