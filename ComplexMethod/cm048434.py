def _log_message(self, record, move, template, vals):
        data = vals.copy()
        if 'lot_id' in vals and vals['lot_id'] != move.lot_id.id:
            data['lot_name'] = self.env['stock.lot'].browse(vals.get('lot_id')).name
        if 'location_id' in vals:
            data['location_name'] = self.env['stock.location'].browse(vals.get('location_id')).name
        if 'location_dest_id' in vals:
            data['location_dest_name'] = self.env['stock.location'].browse(vals.get('location_dest_id')).name
        if 'package_id' in vals and vals['package_id'] != move.package_id.id:
            data['package_name'] = self.env['stock.package'].browse(vals.get('package_id')).name
        if 'package_result_id' in vals and vals['package_result_id'] != move.package_result_id.id:
            data['result_package_dest_name'] = self.env['stock.package'].browse(vals.get('result_package_id')).name
        if 'owner_id' in vals and vals['owner_id'] != move.owner_id.id:
            data['owner_name'] = self.env['res.partner'].browse(vals.get('owner_id')).name
        record.message_post_with_source(
            template,
            render_values={'move': move, 'vals': dict(vals, **data)},
            subtype_xmlid='mail.mt_note',
        )