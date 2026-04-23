def _compute_recipient_single_stored(self):
        for composer in self:
            records = composer._get_records()
            if not records or not composer.comment_single_recipient:
                composer.recipient_single_number_itf = ''
                continue
            records.ensure_one()
            # If the composer was opened with a specific field use that, otherwise get the partner's
            res = records._sms_get_recipients_info(force_field=composer.number_field_name, partner_fallback=not composer.number_field_name)
            if not composer.recipient_single_number_itf:
                composer.recipient_single_number_itf = res[records.id]['sanitized'] or res[records.id]['number'] or ''
            if not composer.number_field_name:
                composer.number_field_name = res[records.id]['field_store']