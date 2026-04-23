def phone_parse(number, country_code):
        try:
            # Parse a first time to obtain an initial PhoneNumber object
            phone_nbr = phonenumbers.parse(number, region=country_code or None, keep_raw_input=True)
            # Force format to international to apply metadata patches
            formatted_intl = phonenumbers.format_number(phone_nbr, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            # Parse a second time with the number now formatted internationally
            phone_nbr = phonenumbers.parse(formatted_intl, region=country_code or None, keep_raw_input=True)
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise UserError(
                _lt('Unable to parse %(phone)s: %(error)s', phone=number, error=str(e))
            ) from e

        if not phonenumbers.is_possible_number(phone_nbr):
            reason = phonenumbers.is_possible_number_with_reason(phone_nbr)
            if reason == phonenumbers.ValidationResult.INVALID_COUNTRY_CODE:
                raise UserError(_lt('Impossible number %s: not a valid country prefix.', number))
            if reason == phonenumbers.ValidationResult.TOO_SHORT:
                raise UserError(_lt('Impossible number %s: not enough digits.', number))
            # in case of "TOO_LONG", we may try to reformat the number in case it was
            # entered without '+' prefix or using leading '++' not always recognized;
            # in any case final error should keep the original number to ease tracking
            if reason == phonenumbers.ValidationResult.TOO_LONG:
                # people may enter 0033... instead of +33...
                if number.startswith('00'):
                    try:
                        phone_nbr = phone_parse(f'+{number.removeprefix("00")}', country_code)
                    except UserError:
                        raise UserError(_lt('Impossible number %s: too many digits.', number))
                # people may enter 33... instead of +33...
                elif not number.startswith('+'):
                    try:
                        phone_nbr = phone_parse(f'+{number}', country_code)
                    except UserError:
                        raise UserError(_lt('Impossible number %s: too many digits.', number))
                else:
                    raise UserError(_lt('Impossible number %s: too many digits.', number))
            else:
                raise UserError(_lt("The phone number %s is invalid! Let's fix it - you are not dialing aliens.", number))
        if not phonenumbers.is_valid_number(phone_nbr):
            raise UserError(_lt('Invalid number %s: probably incorrect prefix.', number))

        return phone_nbr