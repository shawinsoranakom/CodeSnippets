def _get_possible_batches_domain(self):
        self.ensure_one()
        domain = [
            ('state', 'in', ('draft', 'in_progress') if self.picking_type_id.batch_auto_confirm else ('draft',)),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('company_id', '=', self.company_id.id if self.company_id else False),
            ('is_wave', '=', False)
        ]
        if self.picking_type_id.batch_group_by_partner:
            domain.append(('picking_ids.partner_id', '=', self.partner_id.id))
        if self.picking_type_id.batch_group_by_destination:
            domain.append(('picking_ids.partner_id.country_id', '=', self.partner_id.country_id.id))
        if self.picking_type_id.batch_group_by_src_loc:
            domain.append(('picking_ids.location_id', '=', self.location_id.id))
        if self.picking_type_id.batch_group_by_dest_loc:
            domain.append(('picking_ids.location_dest_id', '=', self.location_dest_id.id))
        if self.env.context.get('batches_to_validate'):
            domain.append(('id', 'not in', self.env.context.get('batches_to_validate')))

        return Domain(domain)