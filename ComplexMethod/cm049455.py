def _compute_sanitized_numbers(self):
        for composer in self:
            if composer.numbers:
                record = composer._get_records() if composer.res_model and composer.res_id else self.env.user
                numbers = [number.strip() for number in composer.numbers.split(',')]
                sanitized_numbers = [record._phone_format(number=number) for number in numbers]
                invalid_numbers = [number for sanitized, number in zip(sanitized_numbers, numbers) if not sanitized]
                if invalid_numbers:
                    raise UserError(_('Following numbers are not correctly encoded: %s', repr(invalid_numbers)))
                composer.sanitized_numbers = ','.join(sanitized_numbers)
            else:
                composer.sanitized_numbers = False