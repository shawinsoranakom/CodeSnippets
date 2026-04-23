def _compute_is_visible_on_website(self):
        if all(event.website_visibility == 'public' for event in self):
            self.is_visible_on_website = True
            return
        for event in self:
            if event.website_visibility == 'public' or event.is_participating:
                event.is_visible_on_website = True
            elif not self.env.user._is_public() and event.website_visibility == 'logged_users':
                event.is_visible_on_website = True
            else:
                event.is_visible_on_website = False