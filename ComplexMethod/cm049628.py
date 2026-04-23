def create(self, vals_list):
        ''' In case a menu without a website_id is trying to be created, we duplicate
            it for every website.
            Note: Particularly useful when installing a module that adds a menu like
                  /shop. So every website has the shop menu.
                  Be careful to return correct record for ir.model.data xml_id in case
                  of default main menus creation.
        '''
        self.env.registry.clear_cache('templates')
        # Only used when creating website_data.xml default menu
        menus = self.env['website.menu']
        for vals in vals_list:
            if vals.get('url') == '/default-main-menu':
                menus |= super().create(vals)
                continue
            if 'website_id' in vals:
                menus |= super().create(vals)
                continue
            elif self.env.context.get('website_id'):
                vals['website_id'] = self.env.context.get('website_id')
                menus |= super().create(vals)
                continue
            else:
                # if creating a default menu, we should also save it as such
                default_menu = self.env.ref('website.main_menu', raise_if_not_found=False)
                # create for every site
                w_vals = []
                for website in self.env["website"].search([]):
                    parent_id = vals.get("parent_id")
                    if not parent_id or (default_menu and parent_id == default_menu.id):
                        parent_id = website.menu_id.id
                    w_vals.append({
                        **vals,
                        'website_id': website.id,
                        'parent_id': parent_id,
                    })
                new_menu = super().create(w_vals)[-1:]  # take the last record
                if default_menu and vals.get('parent_id') == default_menu.id:
                    new_menu = super().create(vals)
                menus |= new_menu
        # Only one record per vals is returned but multiple could have been created
        return menus