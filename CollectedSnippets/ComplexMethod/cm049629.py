def _compute_visible(self):
        for menu in self:
            visible = True
            if menu.page_id and not menu.env.user._is_internal():
                page_sudo = menu.page_id.sudo()
                if (not page_sudo.is_visible
                    or (not page_sudo.view_id._handle_visibility(do_raise=False)
                        and page_sudo.view_id._get_cached_visibility() != "password")):
                    visible = False

            if menu.controller_page_id and not menu.env.user._is_internal():
                controller_page_sudo = menu.controller_page_id.sudo()
                if (not controller_page_sudo.is_published
                    or (not controller_page_sudo.view_id._handle_visibility(do_raise=False)
                        and controller_page_sudo.view_id._get_cached_visibility() != "password")):
                    visible = False

            menu.is_visible = visible