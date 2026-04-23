def unlink(self):
        '''This implements COU (copy-on-unlink). When deleting a generic page
        website-specific pages will be created so only the current
        website is affected.
        '''
        current_website_id = self.env.context.get('website_id')

        if current_website_id and not self.env.context.get('no_cow'):
            for view in self.filtered(lambda view: not view.website_id):
                for w in self.env['website'].search([('id', '!=', current_website_id)]):
                    # reuse the COW mechanism to create
                    # website-specific copies, it will take
                    # care of creating pages and menus.
                    view.with_context(website_id=w.id).write({'name': view.name})

        specific_views = self.env['ir.ui.view']
        if self and self.pool._init:
            for view in self.filtered(lambda view: not view.website_id):
                specific_views += view._get_specific_views()

        result = super(IrUiView, self + specific_views).unlink()
        self.env.registry.clear_cache('templates')
        return result