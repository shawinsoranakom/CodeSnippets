def _update_website_menus(self, menus_update_by_field=None):
        super()._update_website_menus(menus_update_by_field=menus_update_by_field)
        for event in self:
            if event.menu_id and (not menus_update_by_field or event in menus_update_by_field.get('website_track')):
                event._update_website_menu_entry('website_track', 'track_menu_ids', 'track')
            if event.menu_id and (not menus_update_by_field or event in menus_update_by_field.get('website_track_proposal')):
                event._update_website_menu_entry('website_track_proposal', 'track_proposal_menu_ids', 'track_proposal')