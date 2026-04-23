def _get_domain_locations(self):
        '''
        Parses the context and returns a list of location_ids based on it.
        It will return all stock locations when no parameters are given
        Possible parameters are shop, warehouse, location, compute_child
        '''
        Location = self.env['stock.location']
        Warehouse = self.env['stock.warehouse']

        def _search_ids(model, values):
            ids = set()
            domains = []
            for item in values:
                if isinstance(item, int):
                    ids.add(item)
                else:
                    domains.append(Domain(self.env[model]._rec_name, 'ilike', item))
            if domains:
                ids |= set(self.env[model].search(Domain.OR(domains)).ids)
            return ids

        # We may receive a location or warehouse from the context, either by explicit
        # python code or by the use of dummy fields in the search view.
        # Normalize them into a list.
        location = self.env.context.get('location') or self.env.context.get('search_location')
        if location and not isinstance(location, list):
            location = [location]
        warehouse = self.env.context.get('warehouse_id') or self.env.context.get('search_warehouse')
        if warehouse and not isinstance(warehouse, list):
            warehouse = [warehouse]
        # filter by location and/or warehouse
        if warehouse:
            w_ids = set(Warehouse.browse(_search_ids('stock.warehouse', warehouse)).mapped('view_location_id').ids)
            if location:
                l_ids = _search_ids('stock.location', location)
                parents = Location.browse(w_ids).mapped("parent_path")
                location_ids = {
                    loc.id
                    for loc in Location.browse(l_ids)
                    if any(loc.parent_path.startswith(parent) for parent in parents)
                }
            else:
                location_ids = w_ids
        else:
            if location:
                location_ids = _search_ids('stock.location', location)
            else:
                location_ids = set(Warehouse.search(
                    [('company_id', 'in', self.env.companies.ids)]
                ).mapped('view_location_id').ids)

        return self._get_domain_locations_new(location_ids)