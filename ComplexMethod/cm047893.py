def _check_warn_sms(self):
        warn_sms_pickings = self.browse()
        for picking in self:
            is_delivery = picking.company_id._get_text_validation('sms') \
                    and picking.picking_type_id.code == 'outgoing' \
                    and picking.partner_id.phone
            if is_delivery \
                    and not modules.module.current_test \
                    and not picking.company_id.has_received_warning_stock_sms \
                    and picking.company_id._get_text_validation('sms'):
                warn_sms_pickings |= picking
        return warn_sms_pickings