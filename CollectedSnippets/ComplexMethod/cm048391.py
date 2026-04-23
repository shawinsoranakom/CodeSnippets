def write(self, vals):
        values = vals
        if 'company_id' in values:
            for location in self:
                if location.company_id.id != values['company_id']:
                    raise UserError(_("Changing the company of this record is forbidden at this point, you should rather archive it and create a new one."))
        if 'usage' in values and values['usage'] == 'view':
            if self.mapped('quant_ids'):
                raise UserError(_("This location's usage cannot be changed to view as it contains products."))
        if 'usage' in values:
            modified_locations = self.filtered(lambda l: l.usage != values['usage'])
            reserved_quantities = self.env['stock.quant'].search_count([
                ('location_id', 'in', modified_locations.ids),
                ('quantity', '>', 0),
                ],
                limit=1)
            if reserved_quantities:
                raise UserError(_(
                    "Internal locations having stock can't be converted"
                ))
        if 'active' in values:
            if not values['active']:
                for location in self:
                    warehouses = self.env['stock.warehouse'].search([('active', '=', True), '|', ('lot_stock_id', '=', location.id), ('view_location_id', '=', location.id)], limit=1)
                    if warehouses:
                        raise UserError(_(
                            "You cannot archive location %(location)s because it is used by warehouse %(warehouse)s",
                            location=location.display_name, warehouse=warehouses.display_name))

            if not self.env.context.get('do_not_check_quant'):
                children_location = self.env['stock.location'].with_context(active_test=False).search([('id', 'child_of', self.ids)])
                internal_children_locations = children_location.filtered(lambda l: l.usage == 'internal')
                children_quants = self.env['stock.quant'].search(['&', '|', ('quantity', '!=', 0), ('reserved_quantity', '!=', 0), ('location_id', 'in', internal_children_locations.ids)])
                if children_quants and not values['active']:
                    raise UserError(_(
                        "You can't disable locations %s because they still contain products.",
                        ', '.join(children_quants.mapped('location_id.display_name'))))
                else:
                    super(StockLocation, children_location - self).with_context(do_not_check_quant=True).write({
                        'active': values['active'],
                    })

        res = super().write(values)
        self.invalidate_model(['warehouse_id'])
        return res