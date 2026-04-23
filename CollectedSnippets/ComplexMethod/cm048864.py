def _find_candidate(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        """ Return the record in self where the procument with values passed as
        args can be merged. If it returns an empty record then a new line will
        be created.
        """
        description_picking = ''
        if values.get('product_description_variants'):
            description_picking = values['product_description_variants']
        lines = self.filtered(
            lambda l: l.propagate_cancel == values['propagate_cancel']
            and (l.orderpoint_id in [values['orderpoint_id'], False] if values['orderpoint_id'] and not values['move_dest_ids'] else True)
            and (l.product_uom_id == product_uom if values.get('force_uom') else True)
        )

        # In case 'product_description_variants' is in the values, we also filter on the PO line
        # name. This way, we can merge lines with the same description. To do so, we need the
        # product name in the context of the PO partner.
        if lines and values.get('product_description_variants'):
            partner = self.mapped('order_id.partner_id')[:1]
            product_lang = product_id.with_context(
                lang=partner.lang,
                partner_id=partner.id,
            )
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase
            lines = lines.filtered(lambda l: (l.name == name + '\n' + description_picking) or (values.get('product_description_variants') in (product_lang.name, product_id.with_user(SUPERUSER_ID).name) and l.name == name))
        return lines and lines.sorted(lambda l: l.orderpoint_id)[0] or self.env['purchase.order.line']