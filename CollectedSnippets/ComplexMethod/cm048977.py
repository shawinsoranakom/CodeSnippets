def _get_auto_batch_description(self):
        """ Get the description of the automatically created batch based on the grouped pickings and grouping criteria """
        self.ensure_one()
        description_items = []
        if self.picking_type_id.batch_group_by_partner and self.partner_id:
            description_items.append(self.partner_id.name or '')
        if self.picking_type_id.batch_group_by_destination and self.partner_id.country_id:
            description_items.append(self.partner_id.country_id.name)
        if self.picking_type_id.batch_group_by_src_loc and self.location_id:
            description_items.append(self.location_id.display_name)
        if self.picking_type_id.batch_group_by_dest_loc and self.location_dest_id:
            description_items.append(self.location_dest_id.display_name)
        return ', '.join(description_items)