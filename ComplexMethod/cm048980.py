def action_done(self):
        def has_no_quantity(picking):
            return all(not m.picked or m.product_uom.is_zero(m.quantity) for m in picking.move_ids if m.state not in ('done', 'cancel'))

        def is_empty(picking):
            return all(m.product_uom.is_zero(m.quantity) for m in picking.move_ids if m.state not in ('done', 'cancel'))

        self.ensure_one()
        self._check_company()
        # Empty 'assigned' or 'waiting for another operation' pickings will be removed from the batch when it is validated.
        pickings = self.mapped('picking_ids').filtered(lambda picking: picking.state not in ('cancel', 'done'))
        empty_waiting_pickings = self.mapped('picking_ids').filtered(lambda p: (p.state in ('waiting', 'confirmed') and has_no_quantity(p)) or (p.state == 'assigned' and is_empty(p)))
        pickings = pickings - empty_waiting_pickings

        empty_pickings = pickings.filtered(has_no_quantity)

        # Run sanity_check as a batch and ignore the one in button_validate() since it is done here.
        pickings._sanity_check(separate_pickings=False)
        context = {
            'skip_sanity_check': True,   # Skip sanity_check in pickings button_validate()
            'pickings_to_detach': empty_waiting_pickings.ids,  # Remove 'waiting' pickings from the batch
            'batches_to_validate': self.ids,  # Skip current batch in auto_wave
        }
        if len(empty_pickings) != len(pickings):
            # If some pickings are at least partially done, other pickings (empty & waiting) will be removed from batch without being cancelled in case of no backorder
            pickings = pickings - empty_pickings
            context['pickings_to_detach'] = context['pickings_to_detach'] + empty_pickings.ids

        for picking in pickings:
            picking.message_post(
                body=Markup("<b>%s:</b> %s <a href=#id=%s&view_type=form&model=stock.picking.batch>%s</a>") % (
                    _("Transferred by"),
                    _("Batch Transfer"),
                    picking.batch_id.id,
                    picking.batch_id.name))

        if empty_waiting_pickings:
            self.message_post(body=_(
                "%s was removed from the batch, no quantity processed",
                Markup(', ').join([picking._get_html_link() for picking in empty_waiting_pickings])
            ))

        return pickings.with_context(**context).button_validate()