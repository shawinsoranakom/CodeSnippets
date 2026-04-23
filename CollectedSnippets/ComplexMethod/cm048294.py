def unlink(self):
        """ Override to synchronize event configuration fields with menu deletion. """
        event_updates = {}
        website_event_menus = self.env['website.event.menu'].search([('menu_id', 'in', self.ids)])
        for event_menu in website_event_menus:
            to_update = event_updates.setdefault(event_menu.event_id, list())
            for menu_type, fname in event_menu.event_id._get_menu_type_field_matching().items():
                if event_menu.menu_type == menu_type:
                    to_update.append(fname)

        unlinked_menus = self

        if website_event_menus:
            # Manually remove website_event_menus to call their ``unlink`` method. Otherwise
            # super unlinks at db level and skip model-specific behavior.
            # Since website.event.menu unlink removes:
            # - the related ir.ui.view records
            # - which cascade deletes the website.page records
            # - which cascade deletes the website.menu records
            # -> we only call super unlink on the remaining website.menu records
            cascaded_menus = website_event_menus.view_id.page_ids.menu_ids
            unlinked_menus = self - cascaded_menus
            website_event_menus.unlink()

        res = super(WebsiteMenu, unlinked_menus).unlink()

        # update events
        for event, to_update in event_updates.items():
            if to_update:
                event.write(dict((fname, False) for fname in to_update))

        return res