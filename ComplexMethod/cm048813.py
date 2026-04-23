def parse_gs1_rule_pattern(self, match, rule):
        result = {
            'rule': rule,
            'type': rule.type,
            'ai': match.group(1),
            'string_value': match.group(2),
        }
        if rule.gs1_content_type == 'measure':
            try:
                decimal_position = 0  # Decimal position begins at the end, 0 means no decimal.
                if rule.gs1_decimal_usage:
                    decimal_position = int(match.group(1)[-1])
                if decimal_position > 0:
                    result['value'] = float(match.group(2)[:-decimal_position] + "." + match.group(2)[-decimal_position:])
                else:
                    result['value'] = int(match.group(2))
            except Exception:
                raise ValidationError(_(
                    "There is something wrong with the barcode rule \"%s\" pattern.\n"
                    "If this rule uses decimal, check it can't get sometime else than a digit as last char for the Application Identifier.\n"
                    "Check also the possible matched values can only be digits, otherwise the value can't be casted as a measure.",
                    rule.name))
        elif rule.gs1_content_type == 'identifier':
            # Check digit and remove it of the value
            if match.group(2)[-1] != str(get_barcode_check_digit("0" * (18 - len(match.group(2))) + match.group(2))):
                return None
            result['value'] = match.group(2)
        elif rule.gs1_content_type == 'date':
            if len(match.group(2)) != 6:
                return None
            result['value'] = self.gs1_date_to_date(match.group(2))
        else:  # when gs1_content_type == 'alpha':
            result['value'] = match.group(2)
        return result