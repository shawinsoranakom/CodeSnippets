def _get_message_values(self):
        """ Return the source, destination and picking_type applied on a stock
        rule. The purpose of this function is to avoid code duplication in
        _get_message_dict functions since it often requires those data.
        """
        source = self.location_src_id and self.location_src_id.display_name or _('Source Location')
        destination = self.location_dest_id and self.location_dest_id.display_name or _('Destination Location')
        direct_destination = self.picking_type_id and self.picking_type_id.default_location_dest_id != self.location_dest_id and self.picking_type_id.default_location_dest_id.display_name
        operation = self.picking_type_id and self.picking_type_id.name or _('Operation Type')
        return source, destination, direct_destination, operation