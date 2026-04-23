def _get_picking_type(self):
        companies = self.company_id or self.env.company
        if not self:
            # default case
            default_warehouse = self.env.user.with_company(companies.id)._get_default_warehouse_id()
            if default_warehouse and default_warehouse.repair_type_id:
                return {(companies, self.env.user): default_warehouse.repair_type_id}

        picking_type_by_company_user = {}
        without_default_warehouse_companies = set()
        for company, user in unique((r.company_id, r.user_id) for r in self):
            default_warehouse = user.with_company(company.id)._get_default_warehouse_id()
            if default_warehouse and default_warehouse.repair_type_id:
                picking_type_by_company_user[(company, user)] = default_warehouse.repair_type_id
            else:
                without_default_warehouse_companies.add(company.id)

        if not without_default_warehouse_companies:
            return picking_type_by_company_user

        domain = [
            ('code', '=', 'repair_operation'),
            ('warehouse_id.company_id', 'in', list(without_default_warehouse_companies)),
        ]

        picking_types = self.env['stock.picking.type'].search_read(domain, ['company_id'], load=False)
        for picking_type in picking_types:
            if (picking_type.company_id, False) not in picking_type_by_company_user:
                picking_type_by_company_user[(picking_type.company_id, False)] = picking_type
        return picking_type_by_company_user