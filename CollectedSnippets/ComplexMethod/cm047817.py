def _post_run_manufacture(self, post_production_values):
        note_subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
        for production, procurement in zip(self, post_production_values):
            if group_id := procurement.values.get('production_group_id'):
                production.production_group_id.parent_ids = [Command.link(group_id)]
            orderpoint = production.orderpoint_id
            origin_production = production.move_dest_ids.raw_material_production_id
            if orderpoint and orderpoint.create_uid.id == api.SUPERUSER_ID and orderpoint.trigger == 'manual':
                production.message_post(
                    body=_('This production order has been created from Replenishment Report.'),
                    message_type='comment',
                    subtype_id=note_subtype_id
                )
            elif orderpoint:
                production.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': production, 'origin': orderpoint},
                    subtype_id=note_subtype_id,
                )
            elif origin_production:
                production.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': production, 'origin': origin_production},
                    subtype_id=note_subtype_id,
                )
        return True