def _find_or_create_global_route(self, xml_id, route_name, create=True, raise_if_not_found=False):
        """ return a route record set from an xml_id or its name. """
        data_route = route = self.env.ref(xml_id, raise_if_not_found=False)
        company = self.company_id[:1] or self.env.company
        if not route or (route.sudo().company_id and route.sudo().company_id != company):
            route = self.env['stock.route'].with_context(active_test=False).search([
                ('name', 'like', route_name), ('company_id', 'in', [False, company.id])
            ], order='company_id', limit=1)
        if not route:
            if raise_if_not_found:
                raise UserError(_('Can\'t find any generic route %s.', route_name))
            elif data_route and create:
                route = data_route.copy({'name': route_name, 'company_id': company.id, 'rule_ids': False})
        return route