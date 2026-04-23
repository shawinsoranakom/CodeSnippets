def register_attendee(self, barcode, event_id):
        attendee = self.search([('barcode', '=', barcode)], limit=1)
        if not attendee:
            return {'error': 'invalid_ticket'}
        res = attendee._get_registration_summary()
        if attendee.state == 'cancel':
            status = 'canceled_registration'
        elif attendee.state == 'draft':
            status = 'unconfirmed_registration'
        elif attendee.event_id.is_finished:
            status = 'not_ongoing_event'
        elif attendee.state != 'done':
            if event_id and attendee.event_id.id != event_id:
                status = 'need_manual_confirmation'
            else:
                attendee.action_set_done()
                status = 'confirmed_registration'
        else:
            status = 'already_registered'
        res.update({'status': status})
        return res