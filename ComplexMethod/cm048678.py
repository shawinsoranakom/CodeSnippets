def _autopost_bill(self):
        # Verify if the bill should be autoposted, if so, post it
        self.ensure_one()
        if (
            self.company_id.autopost_bills
            and self.partner_id
            and self.is_purchase_document(include_receipts=True)
            and self.partner_id.autopost_bills == 'always'
            and not self.abnormal_amount_warning
            and not self.restrict_mode_hash_table
        ):
            if self.duplicated_ref_ids:
                self.message_post(body=_("Auto-post was disabled on this invoice because a potential duplicate was detected."))
            else:
                self.action_post()