def _compute_recipients(self):
        for composer in self:
            composer.recipient_valid_count = 0
            composer.recipient_invalid_count = 0

            if composer.composition_mode not in ('comment', 'mass') or not composer.res_model:
                continue

            records = composer._get_records()
            if records:
                res = records._sms_get_recipients_info(force_field=composer.number_field_name, partner_fallback=not composer.comment_single_recipient)
                composer.recipient_valid_count = len([rid for rid, rvalues in res.items() if rvalues['sanitized']])
                composer.recipient_invalid_count = len([rid for rid, rvalues in res.items() if not rvalues['sanitized']])
            else:
                composer.recipient_invalid_count = 0 if (
                    composer.sanitized_numbers or composer.composition_mode == 'mass'
                ) else 1