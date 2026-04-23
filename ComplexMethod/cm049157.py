def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('form_view_ref') == 'sale_project.sale_order_line_view_form_editable':
            default_values = {
                'name': _("New Sales Order Item"),
            }
            # If we can't add order lines to the default order, discard it
            if 'order_id' in res:
                try:
                    self.env['sale.order'].browse(res['order_id']).check_access('write')
                except AccessError:
                    del res['order_id']

            if 'order_id' in fields and not res.get('order_id'):
                assert (partner_id := self.env.context.get('default_partner_id'))
                project_id = self.env.context.get('link_to_project')
                sale_order = None
                so_create_values = {
                    'partner_id': partner_id,
                    'company_id': self.env.context.get('default_company_id') or self.env.company.id,
                }
                if project_id:
                    try:
                        project_so = self.env['project.project'].browse(project_id).sale_order_id
                        project_so.check_access('write')
                        sale_order = project_so or self.env['sale.order'].search([('project_id', '=', project_id)], limit=1)
                    except AccessError:
                        pass
                    if not sale_order:
                        so_create_values['project_ids'] = [Command.link(project_id)]

                if not sale_order:
                    sale_order = self.env['sale.order'].create(so_create_values)
                default_values['order_id'] = sale_order.id
            return {**res, **default_values}
        return res