def _send_confirmation_email(self):
        # The carrier's API processes validity checks and parcels generation one picking at a time.
        # However, since a UserError of any of the picking will cause a rollback of the entire batch
        # on Odoo's side and since pickings that were already processed on the carrier's side must
        # stay validated, UserErrors might need to be replaced by activity warnings.

        processed_carrier_picking = False

        for pick in self:
            try:
                if pick.carrier_id and pick.carrier_id.integration_level == 'rate_and_ship' and pick.picking_type_code != 'incoming' and not pick.carrier_tracking_ref and pick.picking_type_id.print_label:
                    pick.sudo().send_to_shipper()
                pick._check_carrier_details_compliance()
                if pick.carrier_id:
                    processed_carrier_picking = True
            except (UserError) as e:
                if processed_carrier_picking:
                    # We can not raise a UserError at this point
                    exception_message = str(e)
                    pick.message_post(body=exception_message, message_type='notification')
                    pick.sudo().activity_schedule(
                        'mail.mail_activity_data_warning',
                        date.today(),
                        note=pick._carrier_exception_note(exception_message),
                        user_id=pick.user_id.id or self.env.uid,
                        )
                else:
                    raise e

        return super(StockPicking, self)._send_confirmation_email()