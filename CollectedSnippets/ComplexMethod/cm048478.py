def _prepare_procurement_values(self):
        """ Prepare specific key for moves or other componenets that will be created from a stock rule
        comming from a stock move. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        self.ensure_one()

        product_id = self.product_id.with_context(lang=self._get_lang())
        dates_info = {'date_planned': self._get_mto_procurement_date()}
        route = self.route_ids
        if not route:
            related_packages = self.env['stock.package'].search_fetch([('id', 'parent_of', self.move_line_ids.result_package_id.ids)], ['package_type_id'])
            route = related_packages.package_type_id.route_ids
        if self.location_id.warehouse_id and self.location_id.warehouse_id.lot_stock_id.parent_path in self.location_id.parent_path:
            dates_info = self.product_id._get_dates_info(self.date, self.location_id, route_ids=route)
        warehouse = self.warehouse_id or self.picking_type_id.warehouse_id
        if not self.location_id.warehouse_id:
            warehouse = self.rule_id.route_id.supplier_wh_id

        move_dest_ids = False
        if self.procure_method == "make_to_order":
            move_dest_ids = self
        return {
            # TODO CLPI: maybe make this a little cleaner
            'product_description_variants': self.description_picking and self.description_picking.replace(product_id._get_description(self.picking_type_id), '').replace(product_id._get_picking_description(self.picking_type_id) or '', ''),
            'never_product_template_attribute_value_ids': self.never_product_template_attribute_value_ids,
            'date_planned': dates_info.get('date_planned'),
            'date_order': dates_info.get('date_order'),
            'date_deadline': self.date_deadline,
            'move_dest_ids': move_dest_ids,
            'partner_id': self._get_partner_id() if self.rule_id.procure_method in ('make_to_order', 'mts_else_mto') else False,
            'route_ids': route,
            'warehouse_id': warehouse,
            'priority': self.priority,
            'reference_ids': self.reference_ids,
            'orderpoint_id': self.orderpoint_id,
            'packaging_uom_id': self.packaging_uom_id,
            'procurement_values': self.procurement_values,
        }