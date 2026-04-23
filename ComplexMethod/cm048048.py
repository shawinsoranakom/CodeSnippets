def _update_event_booths(self, set_paid=False):
        for so_line in self.filtered(lambda sol: sol.product_id.service_tracking == 'event_booth'):
            if so_line.event_booth_pending_ids and not so_line.event_booth_ids:
                unavailable = so_line.event_booth_pending_ids.filtered(lambda booth: not booth.is_available)
                if unavailable:
                    raise ValidationError(
                        _('The following booths are unavailable, please remove them to continue : %(booth_names)s',
                          booth_names=''.join('\n\t- %s' % booth.display_name for booth in unavailable)))
                so_line.event_booth_registration_ids.sudo().action_confirm()
            if so_line.event_booth_ids and set_paid:
                so_line.event_booth_ids.sudo().action_set_paid()
        return True